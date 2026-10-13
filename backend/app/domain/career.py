"""Career suggestions follow the skill graph.

A model may explain them. It may not invent requirements.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog import ROLES, get_concept


@dataclass(frozen=True)
class RoleMatch:
    title: str
    summary: str
    readiness: int
    missing: tuple[str, ...]


def match_roles(mastery: dict[str, int]) -> list[RoleMatch]:
    matches: list[RoleMatch] = []
    for role in ROLES:
        scores = [mastery.get(slug, 0) for slug in role.requires]
        readiness = int(round(sum(scores) / len(scores))) if scores else 0
        missing = tuple(
            get_concept(slug).name  # type: ignore[union-attr]
            for slug in role.requires
            if mastery.get(slug, 0) < 75 and get_concept(slug) is not None
        )
        matches.append(RoleMatch(role.title, role.summary, readiness, missing))
    matches.sort(key=lambda item: item.readiness, reverse=True)
    return matches
