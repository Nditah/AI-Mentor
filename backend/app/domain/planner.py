"""Study plans are a topological walk of the goal, not a generated essay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.catalog import detect_concept, get_concept
from app.domain.graph import expand_with_prerequisites, recommend
from app.domain.personalisation import plan_gap_days, plan_limit, preferred_domains


@dataclass(frozen=True)
class PlanItem:
    slug: str
    title: str
    scheduled_for: date


def build_study_plan(
    goal: str,
    mastery: dict[str, int],
    start: date,
    limit: int = 14,
    weekly_minutes: int | None = None,
    career_goal: str | None = None,
) -> list[PlanItem]:
    cap = plan_limit(weekly_minutes) if weekly_minutes is not None else limit
    gap = plan_gap_days(weekly_minutes)
    detected = detect_concept(goal)
    seeds = (
        [detected.slug]
        if detected is not None
        else [
            item.slug
            for item in recommend(mastery, limit=cap, prefer_domains=preferred_domains(career_goal))
        ]
    )
    ordered = [slug for slug in expand_with_prerequisites(seeds) if mastery.get(slug, 0) < 75]
    items: list[PlanItem] = []
    for offset, slug in enumerate(ordered[:cap]):
        concept = get_concept(slug)
        if concept is None:
            continue
        items.append(
            PlanItem(
                slug=slug,
                title=concept.name,
                scheduled_for=start + timedelta(days=offset * gap),
            )
        )
    return items
