"""Registered source connectors for the Resource Catalog.

A connector returns catalog-shaped dictionaries. Network I/O lives in the
service layer; this module names the connector, the stages it runs, and how a
manual or bulk payload is normalised. Harvest connectors never invent records
when the remote call is skipped: they return an empty collection.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.knowledge.taxonomy import SOURCES, SourceDef
from app.domain.knowledge.vocabulary import RESOURCE_TYPES

CONNECTORS = (
    "pack",
    "manual",
    "bulk_json",
    "learn_catalog",
    "catalog_api",
    "ocw",
    "web",
    "hub",
    "docs",
    "kaggle",
    "arxiv",
    "pwc",
    "github",
)


@dataclass(frozen=True)
class ConnectorSpec:
    slug: str
    collection: str
    supports_schedule: bool
    notes: str


SPECS: dict[str, ConnectorSpec] = {
    "pack": ConnectorSpec("pack", "seed files", False, "Knowledge Pack compiler."),
    "manual": ConnectorSpec("manual", "staff form", False, "One record entered in Content Studio."),
    "bulk_json": ConnectorSpec("bulk_json", "JSON array", False, "Staff-uploaded seed file."),
    "learn_catalog": ConnectorSpec(
        "learn_catalog", "Microsoft Learn Catalog API", True, "Modules and learning paths."
    ),
    "catalog_api": ConnectorSpec(
        "catalog_api", "Partner course catalog", True, "Coursera, edX, and similar."
    ),
    "ocw": ConnectorSpec("ocw", "MIT OpenCourseWare", True, "Courses, notes, and lecture videos."),
    "web": ConnectorSpec("web", "Public course pages", True, "Stanford, DeepLearning.AI, fast.ai."),
    "hub": ConnectorSpec("hub", "Hugging Face Hub", True, "Models, datasets, and papers."),
    "docs": ConnectorSpec("docs", "Vendor documentation", True, "PyTorch, ROS, OpenAI, Anthropic."),
    "kaggle": ConnectorSpec("kaggle", "Kaggle API", True, "Datasets and competitions."),
    "arxiv": ConnectorSpec("arxiv", "arXiv API", True, "cs.LG, cs.AI, cs.CV, cs.CL, cs.RO."),
    "pwc": ConnectorSpec("pwc", "Papers with Code", True, "Paper–code–dataset links."),
    "github": ConnectorSpec("github", "GitHub API", True, "README, licence, default branch SHA."),
}


def connector_of(source: SourceDef) -> ConnectorSpec:
    spec = SPECS.get(source.connector)
    if spec is None:
        raise KeyError(source.connector)
    return spec


def sources_due(connector: str | None = None) -> tuple[SourceDef, ...]:
    found = []
    for source in SOURCES:
        if source.schedule == "manual":
            continue
        if connector and source.connector != connector:
            continue
        found.append(source)
    return tuple(found)


def normalise_bulk(payload: list[dict] | dict) -> list[dict]:
    """Accept a bare array or `{ "resources": [...] }` from a staff upload."""

    if isinstance(payload, dict):
        if "resources" in payload and isinstance(payload["resources"], list):
            return list(payload["resources"])
        return [payload]
    return list(payload)


def validate_connector_payload(raw: dict) -> str | None:
    title = str(raw.get("title") or "").strip()
    url = str(raw.get("url") or "").strip()
    resource_type = str(raw.get("resource_type") or raw.get("kind") or "").strip()
    if len(title) < 3:
        return "Each imported record needs a title."
    if (
        resource_type
        and resource_type not in RESOURCE_TYPES
        and resource_type
        not in {
            "lesson",
            "notes",
            "quiz",
            "guide",
            "code",
            "link",
        }
    ):
        return "Unknown resource type."
    if not url and resource_type not in {"learning_path", "coding_challenge", ""}:
        return "Remote sources must include a URL so a learner can open the original."
    return None
