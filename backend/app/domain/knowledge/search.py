"""Catalog search ranking.

Lexical overlap on `search_text`, then facet filters, then a stable rank:

    0.45 lexical + 0.20 quality + 0.15 type/style + 0.10 difficulty fit + 0.10 recency proxy

Semantic neighbours from catalog embeddings, when present, are fused by the
service layer with reciprocal rank fusion. This module never talks to Qdrant.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.embeddings import tokenize
from app.domain.knowledge.asset import AssetRecord, difficulty_delta
from app.domain.knowledge.vocabulary import FREE_COSTS, RESOURCE_TYPES, modality

STYLE_TYPES = {
    "visual": {"video"},
    "reading": {"book", "paper", "blog", "documentation"},
    "hands_on": {"repository", "dataset", "coding_challenge", "tutorial"},
    "auditory": {"podcast"},
    "balanced": set(RESOURCE_TYPES),
}


@dataclass(frozen=True)
class SearchQuery:
    text: str = ""
    topic: str | None = None
    skill: str | None = None
    concept: str | None = None
    difficulty: str | None = None
    resource_type: str | None = None
    provider: str | None = None
    language: str | None = None
    category: str | None = None
    cost: str | None = None
    learning_style: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class SearchHit:
    record: AssetRecord
    score: float
    reasons: tuple[str, ...] = ()


def matches_facets(record: AssetRecord, query: SearchQuery) -> bool:
    if query.resource_type and record.resource_type != query.resource_type:
        return False
    if query.category and record.category != query.category:
        return False
    if query.topic and query.topic not in {record.topic, record.subcategory, record.category}:
        if query.topic not in record.tags and query.topic not in record.concepts:
            return False
    if query.skill and query.skill not in record.skills:
        return False
    if query.concept and query.concept not in record.concepts and query.concept != record.topic:
        return False
    if query.difficulty and record.difficulty != query.difficulty:
        return False
    if query.provider and record.provider.lower() != query.provider.lower():
        return False
    if query.language and record.language != query.language:
        return False
    if query.cost == "free_only" and record.cost_type not in FREE_COSTS:
        return False
    if query.learning_style:
        allowed = STYLE_TYPES.get(query.learning_style, set(RESOURCE_TYPES))
        if record.resource_type not in allowed and modality(record.resource_type) != "mixed":
            return False
    return True


def lexical_score(query: str, record: AssetRecord) -> float:
    tokens = tokenize(query)
    if not tokens:
        return 0.0
    haystack = tokenize(
        " ".join(
            [
                record.title,
                record.title,
                record.description,
                " ".join(record.tags),
                " ".join(record.concepts),
                record.provider,
            ]
        )
    )
    if not haystack:
        return 0.0
    hits = sum(1 for token in tokens if token in haystack)
    return hits / len(tokens)


def rank_record(record: AssetRecord, query: SearchQuery) -> float:
    lexical = lexical_score(query.text, record) if query.text else 0.5
    quality = max(0, min(record.quality_score, 100)) / 100
    type_bonus = 0.0
    if query.resource_type and record.resource_type == query.resource_type:
        type_bonus = 1.0
    elif query.learning_style:
        allowed = STYLE_TYPES.get(query.learning_style, set())
        type_bonus = 1.0 if record.resource_type in allowed else 0.4
    else:
        type_bonus = 0.5
    delta = abs(difficulty_delta(record.difficulty, query.difficulty))
    difficulty_fit = 1.0 if delta == 0 else (0.6 if delta == 1 else 0.2)
    recency = 0.7 if record.publication_date else 0.4
    return (
        0.45 * lexical + 0.20 * quality + 0.15 * type_bonus + 0.10 * difficulty_fit + 0.10 * recency
    )


def search(records: list[AssetRecord], query: SearchQuery) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for record in records:
        if not matches_facets(record, query):
            continue
        if query.text and lexical_score(query.text, record) == 0:
            continue
        score = rank_record(record, query)
        reasons = []
        if query.concept and query.concept in record.concepts:
            reasons.append(f"teaches {query.concept}")
        if query.skill and query.skill in record.skills:
            reasons.append(f"builds {query.skill}")
        hits.append(SearchHit(record, round(score, 4), tuple(reasons)))
    hits.sort(key=lambda item: (-item.score, item.record.title))
    return hits[: max(1, query.limit)]


def reciprocal_rank_fusion(ranked: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Merge ranked id lists. Used when a vector search and a lexical search both run."""

    scores: dict[str, float] = {}
    for listing in ranked:
        for rank, item in enumerate(listing, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
