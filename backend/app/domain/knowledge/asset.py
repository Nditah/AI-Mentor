"""Universal KnowledgeAsset record: validation, slugs, search text, and dedupe keys.

Field names match the seed JSON. The ORM maps `author` to `author_name`,
`estimated_duration` to `estimated_minutes`, `learning_outcomes` to `objectives`,
`ai_generated_summary` to `ai_summary`, `thumbnail` to `thumbnail_url`, and
`metadata` to the `extra` column.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.domain.knowledge.taxonomy import taxonomy_index
from app.domain.knowledge.vocabulary import (
    COST_TYPES,
    DEFAULT_DURATION,
    DURATION_LIMITS,
    LANGUAGES,
    RESOURCE_TYPES,
    SOURCE_TYPES,
    difficulty_rank,
    normalise_language,
)
from app.domain.publishing import DIFFICULTIES, LICENCES

_SLUG = re.compile(r"[^a-z0-9]+")
_SPACE = re.compile(r"\s+")
_TRACKING = frozenset({"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"})
TITLE_MAX = 200
DESCRIPTION_MIN = 20
DESCRIPTION_MAX = 4000


@dataclass
class AssetRecord:
    """One catalog record, independent of the database."""

    title: str
    description: str
    category: str
    resource_type: str
    subcategory: str = ""
    topic: str = ""
    provider: str = ""
    author: str = ""
    url: str = ""
    language: str = "en"
    difficulty: str = "intermediate"
    estimated_duration: int | None = None
    cost_type: str = "free"
    rating: float | None = None
    tags: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    learning_outcomes: list[str] = field(default_factory=list)
    publication_date: str | None = None
    thumbnail: str = ""
    source_type: str = "curated"
    quality_score: int = 0
    ai_generated_summary: str = ""
    metadata: dict = field(default_factory=dict)
    licence: str = "cc-by"
    source: str = "curated-pack"
    external_id: str = ""
    id: str = ""
    concepts: list[str] = field(default_factory=list)

    def duration_minutes(self) -> int:
        if self.estimated_duration is not None:
            return self.estimated_duration
        return DEFAULT_DURATION[self.resource_type]


def canonical_url(url: str) -> str:
    """Lower-case host, drop tracking query params and a trailing slash."""

    raw = (url or "").strip()
    if not raw:
        return ""
    parts = urlsplit(raw)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING
    ]
    path = parts.path.rstrip("/") or ("/" if parts.path else "")
    host = parts.hostname.lower() if parts.hostname else ""
    if parts.port:
        host = f"{host}:{parts.port}"
    scheme = (parts.scheme or "https").lower()
    return urlunsplit((scheme, host, path, urlencode(query), ""))


def slugify(title: str, resource_type: str = "", limit: int = 80) -> str:
    base = _SLUG.sub("-", title.lower()).strip("-")
    prefix = resource_type.replace("_", "-") if resource_type else ""
    if prefix and not base.startswith(prefix):
        base = f"{prefix}-{base}"
    base = base[:limit].rstrip("-")
    return base or "resource"


def search_text(record: AssetRecord) -> str:
    parts = [
        record.title,
        record.description,
        record.category,
        record.subcategory,
        record.topic,
        record.provider,
        record.author,
        record.ai_generated_summary,
        " ".join(record.tags),
        " ".join(record.skills),
        " ".join(record.concepts),
        " ".join(record.learning_outcomes),
    ]
    return _SPACE.sub(" ", " ".join(part for part in parts if part)).strip()


def dedupe_key(record: AssetRecord) -> str:
    """Stable identity. URL, DOI, and arXiv win over a normalised title."""

    extra = record.metadata or {}
    doi = str(extra.get("doi") or "").strip().lower()
    arxiv = str(extra.get("arxiv_id") or "").strip().lower()
    isbn = str(extra.get("isbn") or "").strip().replace("-", "")
    if doi:
        return f"doi:{doi}"
    if arxiv:
        return f"arxiv:{arxiv}"
    if isbn:
        return f"isbn:{isbn}"
    url = canonical_url(record.url)
    if url:
        return f"url:{url}"
    title = _SPACE.sub(" ", record.title.lower()).strip()
    provider = record.provider.lower().strip()
    raw = f"{record.resource_type}|{title}|{provider}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"title:{digest}"


def parse_publication_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip()
    if len(text) == 4 and text.isdigit():
        return date(int(text), 1, 1)
    if len(text) == 7 and text[4] == "-":
        year, month = text.split("-")
        return date(int(year), int(month), 1)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return date.fromisoformat(text[:10])
    return None


def validate_record(record: AssetRecord) -> str | None:
    """A human message when the record cannot enter the catalog, else None."""

    title = record.title.strip()
    if len(title) < 3 or len(title) > TITLE_MAX:
        return "Title must be 3–200 characters."
    description = record.description.strip()
    if len(description) < DESCRIPTION_MIN or len(description) > DESCRIPTION_MAX:
        return "Description must be 20–4,000 characters."
    if record.resource_type not in RESOURCE_TYPES:
        return "Unknown resource type."
    if record.difficulty not in DIFFICULTIES:
        return "Unknown difficulty."
    if record.cost_type not in COST_TYPES:
        return "Unknown cost type."
    if record.source_type not in SOURCE_TYPES:
        return "Unknown source type."
    language = normalise_language(record.language)
    if language is None:
        return "Unknown language."
    if language not in LANGUAGES:
        return "Unknown language."
    low, high = DURATION_LIMITS[record.resource_type]
    minutes = record.duration_minutes()
    if minutes < low or minutes > high:
        return f"Study time for a {record.resource_type} must be {low}–{high} minutes."
    if record.rating is not None and not 0 <= record.rating <= 5:
        return "Rating must be between 0 and 5."
    if record.licence not in LICENCES:
        return "Choose a licence the library recognises."
    nodes = taxonomy_index()
    if record.category and record.category not in nodes:
        return f"Unknown category {record.category}."
    if record.subcategory and record.subcategory not in nodes:
        return f"Unknown subcategory {record.subcategory}."
    if record.topic and record.topic not in nodes:
        return f"Unknown topic {record.topic}."
    if record.subcategory:
        parent = nodes[record.subcategory].parent
        if parent != record.category:
            return "Subcategory does not belong to that category."
    if record.topic and record.subcategory:
        parent = nodes[record.topic].parent
        if parent != record.subcategory:
            return "Topic does not belong to that subcategory."
    if len(record.tags) > 24 or any(len(tag) > 40 or not tag.strip() for tag in record.tags):
        return "Use at most 24 tags, each up to 40 characters."
    if record.url and not canonical_url(record.url):
        return "URL is not usable."
    return None


def from_mapping(raw: dict) -> AssetRecord:
    """Build a record from seed JSON. Unknown keys stay in metadata."""

    known = {
        "title",
        "description",
        "category",
        "subcategory",
        "topic",
        "resource_type",
        "provider",
        "author",
        "url",
        "language",
        "difficulty",
        "estimated_duration",
        "cost_type",
        "rating",
        "tags",
        "skills",
        "prerequisites",
        "learning_outcomes",
        "publication_date",
        "thumbnail",
        "source_type",
        "quality_score",
        "ai_generated_summary",
        "metadata",
        "licence",
        "source",
        "external_id",
        "id",
        "concepts",
    }
    extra = dict(raw.get("metadata") or {})
    for key, value in raw.items():
        if key not in known:
            extra[key] = value
    language = normalise_language(str(raw.get("language") or "en")) or "en"
    return AssetRecord(
        title=str(raw.get("title") or ""),
        description=str(raw.get("description") or ""),
        category=str(raw.get("category") or ""),
        subcategory=str(raw.get("subcategory") or ""),
        topic=str(raw.get("topic") or ""),
        resource_type=str(raw.get("resource_type") or ""),
        provider=str(raw.get("provider") or ""),
        author=str(raw.get("author") or ""),
        url=str(raw.get("url") or ""),
        language=language,
        difficulty=str(raw.get("difficulty") or "intermediate"),
        estimated_duration=raw.get("estimated_duration"),
        cost_type=str(raw.get("cost_type") or "free"),
        rating=raw.get("rating"),
        tags=list(raw.get("tags") or []),
        skills=list(raw.get("skills") or []),
        prerequisites=list(raw.get("prerequisites") or []),
        learning_outcomes=list(raw.get("learning_outcomes") or []),
        publication_date=raw.get("publication_date"),
        thumbnail=str(raw.get("thumbnail") or ""),
        source_type=str(raw.get("source_type") or "curated"),
        quality_score=int(raw.get("quality_score") or 0),
        ai_generated_summary=str(raw.get("ai_generated_summary") or ""),
        metadata=extra,
        licence=str(raw.get("licence") or "cc-by"),
        source=str(raw.get("source") or "curated-pack"),
        external_id=str(raw.get("external_id") or raw.get("id") or ""),
        id=str(raw.get("id") or ""),
        concepts=list(raw.get("concepts") or []),
    )


def difficulty_delta(resource: str, learner: str | None) -> int:
    """How many bands the resource sits above the learner. Negative is easier."""

    if not learner:
        return 0
    return difficulty_rank(resource) - difficulty_rank(learner)
