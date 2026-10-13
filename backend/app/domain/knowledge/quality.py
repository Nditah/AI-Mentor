"""Quality score for a catalog record.

The score is 0–100. It is a publishing aid, not a learner-facing grade. Weights
follow the scorecard in docs/platform/13: completeness, provenance, freshness
proxies, and whether a human could follow the link.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.knowledge.asset import AssetRecord, canonical_url, parse_publication_date
from app.domain.knowledge.vocabulary import FREE_COSTS, REVIEW_INTERVAL_DAYS
from app.domain.publishing import LICENCES

WEIGHTS = {
    "completeness": 40,
    "provenance": 20,
    "usefulness": 20,
    "freshness": 10,
    "verification": 10,
}


def _completeness(record: AssetRecord) -> float:
    checks = [
        bool(record.title.strip()),
        len(record.description.strip()) >= 40,
        bool(record.category),
        bool(record.topic or record.subcategory),
        bool(record.provider or record.author),
        bool(record.learning_outcomes),
        bool(record.skills or record.concepts),
        bool(record.tags),
        record.estimated_duration is not None,
        bool(
            canonical_url(record.url)
            or record.resource_type in {"learning_path", "coding_challenge"}
        ),
    ]
    return sum(1 for item in checks if item) / len(checks)


def _provenance(record: AssetRecord) -> float:
    score = 0.0
    if record.licence in LICENCES and record.licence != "fair-use-excerpt":
        score += 0.4
    elif record.licence in LICENCES:
        score += 0.2
    if record.author or record.provider:
        score += 0.3
    extra = record.metadata or {}
    if extra.get("doi") or extra.get("arxiv_id") or extra.get("isbn") or extra.get("commit_sha"):
        score += 0.3
    elif canonical_url(record.url):
        score += 0.2
    return min(score, 1.0)


def _usefulness(record: AssetRecord) -> float:
    score = 0.4
    if record.rating is not None:
        score += 0.4 * (record.rating / 5)
    if record.cost_type in FREE_COSTS:
        score += 0.1
    if record.learning_outcomes:
        score += 0.1
    return min(score, 1.0)


def _freshness(record: AssetRecord, *, now: datetime | None = None) -> float:
    published = parse_publication_date(record.publication_date)
    if published is None:
        return 0.5
    today = (now or datetime.now(UTC)).date()
    age_days = max(0, (today - published).days)
    interval = REVIEW_INTERVAL_DAYS.get(record.resource_type, 180)
    if age_days <= interval:
        return 1.0
    if age_days <= interval * 3:
        return 0.6
    return 0.3


def _verification(record: AssetRecord) -> float:
    status = str((record.metadata or {}).get("verification_status") or "unverified")
    return {
        "ok": 1.0,
        "redirected": 0.7,
        "unverified": 0.4,
        "changed": 0.3,
        "broken": 0.0,
        "blocked": 0.0,
    }.get(status, 0.4)


def score_record(record: AssetRecord, *, now: datetime | None = None) -> tuple[int, dict[str, int]]:
    """Weighted 0–100 score and the per-dimension integers that add up to it."""

    parts = {
        "completeness": _completeness(record),
        "provenance": _provenance(record),
        "usefulness": _usefulness(record),
        "freshness": _freshness(record, now=now),
        "verification": _verification(record),
    }
    detail = {name: int(round(parts[name] * weight)) for name, weight in WEIGHTS.items()}
    total = min(100, sum(detail.values()))
    return total, detail
