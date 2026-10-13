"""Duplicate detection for catalog records.

URL, DOI, arXiv, and ISBN collisions are exact. Title collisions use token
overlap so "Deep Learning (Goodfellow)" and "Deep Learning, Goodfellow et al."
surface as a pair for a steward, not an automatic merge.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.embeddings import tokenize
from app.domain.knowledge.asset import AssetRecord, canonical_url, dedupe_key


@dataclass(frozen=True)
class DuplicateHit:
    left_id: str
    right_id: str
    method: str
    score: float
    detail: dict


def _identity(record: AssetRecord) -> dict[str, str]:
    extra = record.metadata or {}
    found = {}
    doi = str(extra.get("doi") or "").strip().lower()
    arxiv = str(extra.get("arxiv_id") or "").strip().lower()
    isbn = str(extra.get("isbn") or "").replace("-", "").strip()
    url = canonical_url(record.url)
    if doi:
        found["doi"] = doi
    if arxiv:
        found["arxiv"] = arxiv
    if isbn:
        found["isbn"] = isbn
    if url:
        found["url"] = url
    found["key"] = dedupe_key(record)
    return found


def jaccard(left: str, right: str) -> float:
    a = set(tokenize(left))
    b = set(tokenize(right))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pair_score(left: AssetRecord, right: AssetRecord) -> DuplicateHit | None:
    """None when the pair is distinct enough to keep both."""

    left_id = left.id or left.external_id or left.title
    right_id = right.id or right.external_id or right.title
    a = _identity(left)
    b = _identity(right)
    for method in ("doi", "arxiv", "isbn", "url", "key"):
        if method in a and a[method] == b.get(method):
            return DuplicateHit(left_id, right_id, method, 1.0, {method: a[method]})
    if left.resource_type != right.resource_type:
        return None
    overlap = jaccard(left.title, right.title)
    same_provider = left.provider.strip().lower() == right.provider.strip().lower() and bool(
        left.provider.strip()
    )
    threshold = 0.72 if same_provider else 0.88
    if overlap >= threshold:
        return DuplicateHit(
            left_id,
            right_id,
            "title",
            round(overlap, 3),
            {"provider_match": same_provider},
        )
    return None


def find_duplicates(records: list[AssetRecord]) -> list[DuplicateHit]:
    """Compare every pair. Fine for a pack; stewards run it on a filtered slice."""

    hits: list[DuplicateHit] = []
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            hit = pair_score(left, right)
            if hit is not None:
                hits.append(hit)
    hits.sort(key=lambda item: item.score, reverse=True)
    return hits
