"""Controlled vocabularies for the Resource Catalog.

The database CHECK constraints in revision 20261013_0002 list the same values. Adding a
value means a new revision as well as an edit here.
"""

from __future__ import annotations

from app.domain.publishing import DIFFICULTIES

RESOURCE_TYPES = (
    "book",
    "course",
    "paper",
    "video",
    "repository",
    "dataset",
    "tutorial",
    "blog",
    "certification",
    "documentation",
    "podcast",
    "learning_path",
    "coding_challenge",
)
RESOURCE_TYPE_LABELS = {
    "book": "Book",
    "course": "Course",
    "paper": "Research paper",
    "video": "Video",
    "repository": "GitHub repository",
    "dataset": "Dataset",
    "tutorial": "Tutorial",
    "blog": "Blog post",
    "certification": "Certification",
    "documentation": "Documentation",
    "podcast": "Podcast",
    "learning_path": "Learning path",
    "coding_challenge": "Coding challenge",
}
COST_TYPES = ("free", "freemium", "free_audit", "paid", "subscription")
FREE_COSTS = frozenset({"free", "freemium", "free_audit"})
SOURCE_TYPES = ("authored", "curated", "harvested", "imported", "ai_generated")
VERIFICATION_STATUSES = ("unverified", "ok", "redirected", "broken", "blocked", "changed")
LEARNING_STYLES = ("visual", "reading", "hands_on", "auditory", "balanced")
RELATION_TYPES = (
    "prerequisite_of",
    "builds_on",
    "related_to",
    "part_of",
    "applies_to",
    "contrasts_with",
)
ACYCLIC_RELATIONS = frozenset({"prerequisite_of", "builds_on", "part_of"})
SYMMETRIC_RELATIONS = frozenset({"related_to", "contrasts_with"})
BLOCKING_WEIGHT = 0.5
DIFFICULTY_RANK = {name: rank for rank, name in enumerate(DIFFICULTIES)}

LANGUAGES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "ar": "Arabic",
    "ru": "Russian",
}
_LANGUAGE_NAMES = {name.lower(): code for code, name in LANGUAGES.items()}

MODALITY = {
    "video": "visual",
    "podcast": "auditory",
    "book": "reading",
    "paper": "reading",
    "blog": "reading",
    "documentation": "reading",
    "repository": "hands_on",
    "dataset": "hands_on",
    "coding_challenge": "hands_on",
    "tutorial": "hands_on",
    "course": "mixed",
    "certification": "mixed",
    "learning_path": "mixed",
}

# Study time bounds in minutes. A book or a certification track runs to weeks.
DURATION_LIMITS = {
    "book": (60, 6000),
    "course": (30, 20000),
    "paper": (10, 600),
    "video": (1, 600),
    "repository": (10, 6000),
    "dataset": (10, 6000),
    "tutorial": (5, 1200),
    "blog": (2, 240),
    "certification": (60, 20000),
    "documentation": (5, 3000),
    "podcast": (5, 600),
    "learning_path": (60, 50000),
    "coding_challenge": (5, 600),
}
DEFAULT_DURATION = {
    "book": 900,
    "course": 1200,
    "paper": 60,
    "video": 45,
    "repository": 120,
    "dataset": 90,
    "tutorial": 45,
    "blog": 15,
    "certification": 2400,
    "documentation": 60,
    "podcast": 60,
    "learning_path": 2400,
    "coding_challenge": 30,
}
# Days between link checks and editorial review. Fast-moving types are checked sooner.
REVIEW_INTERVAL_DAYS = {
    "documentation": 90,
    "repository": 60,
    "course": 120,
    "certification": 90,
    "tutorial": 120,
    "blog": 180,
    "video": 180,
    "podcast": 120,
    "dataset": 120,
    "paper": 365,
    "book": 365,
    "learning_path": 120,
    "coding_challenge": 365,
}

_KIND_TO_TYPE = {
    "paper": "paper",
    "dataset": "dataset",
    "code": "repository",
    "link": "documentation",
}


def resource_type_for_kind(kind: str) -> str:
    """The catalog type an authored library item gets from its stored kind."""

    return _KIND_TO_TYPE.get(kind, "tutorial")


def modality(resource_type: str) -> str:
    return MODALITY.get(resource_type, "mixed")


def normalise_language(value: str | None) -> str | None:
    """`en`, `en-US`, `EN`, and `English` all become `en`. Unknown values return None."""

    if not value:
        return None
    cleaned = value.strip().lower().replace("_", "-")
    code = cleaned.split("-")[0]
    if code in LANGUAGES:
        return code
    return _LANGUAGE_NAMES.get(cleaned)


def difficulty_rank(difficulty: str) -> int:
    return DIFFICULTY_RANK.get(difficulty, DIFFICULTY_RANK["intermediate"])
