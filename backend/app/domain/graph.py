"""Prerequisite graph used by recommendations and study plans."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog import CONCEPTS, concept_index, get_concept

PREREQ_MET_AT = 70
RECOMMEND_BELOW = 75


@dataclass(frozen=True)
class Recommendation:
    slug: str
    name: str
    reason: str


def prerequisites_of(slug: str) -> tuple[str, ...]:
    concept = get_concept(slug)
    if concept is None:
        raise KeyError(slug)
    return concept.prerequisites


def missing_prerequisites(slug: str, mastered: set[str]) -> list[str]:
    return [item for item in prerequisites_of(slug) if item not in mastered]


def topological(slugs: set[str]) -> list[str]:
    """Stable Kahn sort. Raises if the induced prerequisite graph has a cycle."""

    indegree = {slug: 0 for slug in slugs}
    dependents: dict[str, list[str]] = {slug: [] for slug in slugs}
    for slug in slugs:
        for prereq in prerequisites_of(slug):
            if prereq not in slugs:
                continue
            indegree[slug] += 1
            dependents[prereq].append(slug)
    ready = [slug for slug, degree in indegree.items() if degree == 0]
    order: list[str] = []
    while ready:
        ready.sort(key=concept_index)
        node = ready.pop(0)
        order.append(node)
        for child in dependents[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(slugs):
        raise ValueError("prerequisite cycle")
    return order


def expand_with_prerequisites(slugs: list[str]) -> list[str]:
    needed: set[str] = set()
    stack = list(slugs)
    while stack:
        slug = stack.pop()
        if slug in needed:
            continue
        if get_concept(slug) is None:
            continue
        needed.add(slug)
        stack.extend(prerequisites_of(slug))
    return topological(needed)


def recommend(
    mastery: dict[str, int],
    limit: int = 4,
    prefer_domains: tuple[str, ...] = (),
) -> list[Recommendation]:
    preferred: list[Recommendation] = []
    others: list[Recommendation] = []
    for concept in CONCEPTS:
        score = mastery.get(concept.slug, 0)
        if score >= RECOMMEND_BELOW:
            continue
        if not all(mastery.get(item, 0) >= PREREQ_MET_AT for item in concept.prerequisites):
            continue
        if concept.prerequisites:
            names = ", ".join(get_concept(item).name for item in concept.prerequisites)  # type: ignore[union-attr]
            reason = f"Prerequisites met: {names}."
        else:
            reason = "No prerequisites. A sound place to start."
        item = Recommendation(concept.slug, concept.name, reason)
        if prefer_domains and concept.domain in prefer_domains:
            preferred.append(item)
        else:
            others.append(item)
    return (preferred + others)[:limit]


def mermaid(domain: str | None = None) -> str:
    concepts = [concept for concept in CONCEPTS if domain is None or concept.domain == domain]
    slugs = {concept.slug for concept in concepts}
    lines = ["flowchart TD"]
    for concept in concepts:
        lines.append(f'  {concept.slug.replace("-", "_")}["{concept.name}"]')
    for concept in concepts:
        for prereq in concept.prerequisites:
            if prereq not in slugs:
                continue
            lines.append(f"  {prereq.replace('-', '_')} --> {concept.slug.replace('-', '_')}")
    return "\n".join(lines)
