"""Study plans are a topological walk of the goal, not a generated essay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.catalog import detect_concept, get_concept
from app.domain.graph import expand_with_prerequisites, recommend


@dataclass(frozen=True)
class PlanItem:
    slug: str
    title: str
    scheduled_for: date


def build_study_plan(
    goal: str, mastery: dict[str, int], start: date, limit: int = 14
) -> list[PlanItem]:
    detected = detect_concept(goal)
    seeds = (
        [detected.slug]
        if detected is not None
        else [item.slug for item in recommend(mastery, limit=limit)]
    )
    ordered = [slug for slug in expand_with_prerequisites(seeds) if mastery.get(slug, 0) < 75]
    items: list[PlanItem] = []
    for offset, slug in enumerate(ordered[:limit]):
        concept = get_concept(slug)
        if concept is None:
            continue
        items.append(
            PlanItem(slug=slug, title=concept.name, scheduled_for=start + timedelta(days=offset))
        )
    return items
