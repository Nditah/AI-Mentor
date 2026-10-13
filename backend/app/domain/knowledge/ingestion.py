"""Twelve-stage content ingestion pipeline.

Each stage is a pure function. The service layer records `ImportJobItem` rows
and talks to the network. A stage that rejects a record stops the rest of the
pipeline for that record; later stages never see invalid input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.knowledge.asset import (
    AssetRecord,
    dedupe_key,
    from_mapping,
    search_text,
    slugify,
    validate_record,
)
from app.domain.knowledge.graph import KnowledgeGraph
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.taxonomy import SKILLS, category_of, taxonomy_index
from app.domain.knowledge.vocabulary import (
    DEFAULT_DURATION,
    difficulty_rank,
    resource_type_for_kind,
)
from app.domain.publishing import DIFFICULTIES

STAGES = (
    "source_registration",
    "asset_collection",
    "metadata_extraction",
    "content_validation",
    "topic_classification",
    "difficulty_classification",
    "skill_mapping",
    "knowledge_graph_mapping",
    "embedding_generation",
    "catalog_registration",
    "search_indexing",
    "recommendation_registration",
)

OUTCOMES = (
    "created",
    "updated",
    "unchanged",
    "duplicate",
    "rejected",
    "failed",
    "skipped",
)


@dataclass
class PipelineItem:
    reference: str
    title: str = ""
    raw: dict = field(default_factory=dict)
    record: AssetRecord | None = None
    outcome: str = "created"
    stage: str = STAGES[0]
    issues: list[str] = field(default_factory=list)
    search_blob: str = ""
    embedding_text: str = ""
    duplicate_of: str = ""
    quality_score: int = 0
    quality_detail: dict = field(default_factory=dict)


@dataclass
class PipelineContext:
    source_slug: str
    known_keys: dict[str, str] = field(default_factory=dict)
    graph: KnowledgeGraph | None = None
    publish_policy: str = "review"
    trust_level: int = 3


def run_pipeline(raw_items: list[dict], context: PipelineContext) -> list[PipelineItem]:
    """Run every collected record through the twelve stages."""

    results: list[PipelineItem] = []
    seen_in_batch: dict[str, str] = {}
    for position, raw in enumerate(raw_items):
        item = PipelineItem(
            reference=str(raw.get("id") or raw.get("url") or raw.get("title") or position),
            title=str(raw.get("title") or ""),
            raw=dict(raw),
        )
        for stage in STAGES:
            item.stage = stage
            handler = _HANDLERS[stage]
            handler(item, context, seen_in_batch)
            if item.outcome in {"rejected", "failed", "duplicate", "skipped"}:
                break
        results.append(item)
    return results


def _source_registration(item: PipelineItem, context: PipelineContext, _seen: dict) -> None:
    if not context.source_slug:
        item.outcome = "rejected"
        item.issues.append("No content source is registered for this import.")


def _asset_collection(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    if not item.raw.get("title") and not item.raw.get("url"):
        item.outcome = "rejected"
        item.issues.append("A collected asset needs a title or a URL.")


def _metadata_extraction(item: PipelineItem, context: PipelineContext, _seen: dict) -> None:
    raw = dict(item.raw)
    raw.setdefault("source", context.source_slug)
    raw.setdefault(
        "source_type", "imported" if context.source_slug != "curated-pack" else "curated"
    )
    if raw.get("kind") and not raw.get("resource_type"):
        raw["resource_type"] = resource_type_for_kind(str(raw["kind"]))
    record = from_mapping(raw)
    if not record.estimated_duration:
        record.estimated_duration = DEFAULT_DURATION.get(record.resource_type, 45)
    item.record = record
    item.title = record.title


def _content_validation(item: PipelineItem, context: PipelineContext, seen: dict) -> None:
    record = item.record
    if record is None:
        item.outcome = "failed"
        item.issues.append("Metadata extraction produced no record.")
        return
    message = validate_record(record)
    if message:
        item.outcome = "rejected"
        item.issues.append(message)
        return
    key = dedupe_key(record)
    if key in seen:
        item.outcome = "duplicate"
        item.duplicate_of = seen[key]
        item.issues.append("Duplicate of another record in this batch.")
        return
    if key in context.known_keys:
        item.outcome = "duplicate"
        item.duplicate_of = context.known_keys[key]
        item.issues.append("Duplicate of an existing catalog record.")
        return
    seen[key] = record.id or record.external_id or record.title


def _topic_classification(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    nodes = taxonomy_index()
    if record.topic and record.topic in nodes and not record.subcategory:
        parent = nodes[record.topic].parent
        record.subcategory = parent or record.subcategory
    if record.subcategory and record.subcategory in nodes and not record.category:
        record.category = category_of(record.subcategory)
    if not record.category and record.topic:
        record.category = category_of(record.topic)
    if not record.category:
        item.issues.append("Topic classification could not assign a category.")


def _difficulty_classification(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    if record.difficulty not in DIFFICULTIES:
        record.difficulty = "intermediate"
        item.issues.append("Difficulty defaulted to intermediate.")
    hints = " ".join(
        [record.title, record.description, " ".join(record.tags), record.topic]
    ).lower()
    if record.difficulty == "intermediate":
        if any(word in hints for word in ("introduction", "beginner", "primer", "101")):
            record.difficulty = "beginner"
        elif any(word in hints for word in ("advanced", "survey", "state of the art")):
            record.difficulty = "advanced"


def _skill_mapping(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    known = {skill.slug for skill in SKILLS}
    haystack = " ".join(
        [record.title, record.description, " ".join(record.tags), " ".join(record.concepts)]
    ).lower()
    extra = [skill.slug for skill in SKILLS if skill.slug.replace("-", " ") in haystack]
    merged = []
    for slug in list(record.skills) + extra:
        if slug in known and slug not in merged:
            merged.append(slug)
    record.skills = merged[:12]


def _knowledge_graph_mapping(item: PipelineItem, context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    graph = context.graph
    if graph is None:
        return
    linked = [slug for slug in record.concepts if slug in graph.nodes]
    if record.topic in graph.nodes and record.topic not in linked:
        linked.append(record.topic)
    for slug in list(linked):
        for edge in graph.blocking_prerequisites(slug):
            if edge.source not in record.prerequisites:
                record.prerequisites.append(edge.source)
    record.concepts = linked
    if linked:
        hardest = max(linked, key=lambda slug: difficulty_rank(graph.nodes[slug].difficulty))
        if difficulty_rank(graph.nodes[hardest].difficulty) > difficulty_rank(record.difficulty):
            record.difficulty = graph.nodes[hardest].difficulty


def _embedding_generation(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    item.search_blob = search_text(record)
    item.embedding_text = " ".join(
        part for part in (record.title, record.description, record.ai_generated_summary) if part
    )


def _catalog_registration(item: PipelineItem, context: PipelineContext, _seen: dict) -> None:
    record = item.record
    if record is None:
        return
    if not record.id:
        record.id = slugify(record.title, record.resource_type)
    record.quality_score, item.quality_detail = score_record(record)
    item.quality_score = record.quality_score
    if context.trust_level <= 2 and context.publish_policy == "publish":
        item.issues.append("Low-trust source cannot auto-publish; held in review.")


def _search_indexing(item: PipelineItem, _context: PipelineContext, _seen: dict) -> None:
    if not item.search_blob:
        item.issues.append("Search text is empty; the index will be weak.")


def _recommendation_registration(
    item: PipelineItem, _context: PipelineContext, _seen: dict
) -> None:
    record = item.record
    if record is None:
        return
    if not record.concepts and not record.skills:
        item.issues.append("No skills or concepts; recommendations will under-rank this resource.")


_HANDLERS = {
    "source_registration": _source_registration,
    "asset_collection": _asset_collection,
    "metadata_extraction": _metadata_extraction,
    "content_validation": _content_validation,
    "topic_classification": _topic_classification,
    "difficulty_classification": _difficulty_classification,
    "skill_mapping": _skill_mapping,
    "knowledge_graph_mapping": _knowledge_graph_mapping,
    "embedding_generation": _embedding_generation,
    "catalog_registration": _catalog_registration,
    "search_indexing": _search_indexing,
    "recommendation_registration": _recommendation_registration,
}
