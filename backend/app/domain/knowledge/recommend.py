"""Recommend catalog resources from goals, weak skills, career, progress, and style.

Concept eligibility stays in `graph.recommend_concepts`. This module ranks
*resources* a learner should open next. Weights:

    0.35 learning goals / concept match
    0.25 weak skills
    0.20 career goals
    0.10 current progress (eligible concepts only)
    0.10 learning style
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.knowledge.asset import AssetRecord, difficulty_delta
from app.domain.knowledge.graph import KnowledgeGraph, eligibility
from app.domain.knowledge.search import STYLE_TYPES
from app.domain.knowledge.taxonomy import CAREER_ROLES, CareerRoleDef
from app.domain.knowledge.vocabulary import FREE_COSTS, modality
from app.domain.personalisation import career_slug


@dataclass(frozen=True)
class LearnerState:
    mastery: dict[str, int] = field(default_factory=dict)
    goals: tuple[str, ...] = ()
    weak_skills: tuple[str, ...] = ()
    career_goal: str | None = None
    learning_style: str = "balanced"
    preferred_types: tuple[str, ...] = ()
    cost_preference: str = "any"
    languages: tuple[str, ...] = ("en",)
    weekly_minutes: int | None = None


@dataclass(frozen=True)
class ResourceRecommendation:
    record: AssetRecord
    score: float
    reason: str


def career_role(slug: str | None) -> CareerRoleDef | None:
    mapped = career_slug(slug)
    if not mapped:
        return None
    for role in CAREER_ROLES:
        if role.slug == mapped:
            return role
    return None


def _goal_score(record: AssetRecord, state: LearnerState) -> float:
    if not state.goals:
        return 0.4
    haystack = set(record.concepts) | set(record.tags) | {record.topic, record.category}
    hits = sum(1 for goal in state.goals if goal in haystack)
    return hits / len(state.goals) if hits else 0.0


def _skill_score(record: AssetRecord, state: LearnerState) -> float:
    if not state.weak_skills:
        return 0.3
    hits = sum(1 for skill in state.weak_skills if skill in record.skills)
    return hits / len(state.weak_skills) if hits else 0.0


def _career_score(record: AssetRecord, state: LearnerState) -> float:
    role = career_role(state.career_goal)
    if role is None:
        return 0.3
    skill_hits = sum(1 for skill in role.skills if skill in record.skills)
    concept_hits = sum(1 for concept in role.concepts if concept in record.concepts)
    denom = len(role.skills) + len(role.concepts)
    return (skill_hits + concept_hits) / denom if denom else 0.0


def _progress_score(record: AssetRecord, graph: KnowledgeGraph, state: LearnerState) -> float:
    if not record.concepts:
        return 0.4
    eligible = 0
    considered = 0
    for slug in record.concepts:
        if slug not in graph.nodes:
            continue
        considered += 1
        status = eligibility(graph, slug, state.mastery)
        if status.eligible:
            eligible += 1
    if considered == 0:
        return 0.4
    return eligible / considered


def _style_score(record: AssetRecord, state: LearnerState) -> float:
    if state.preferred_types and record.resource_type in state.preferred_types:
        return 1.0
    allowed = STYLE_TYPES.get(state.learning_style, set())
    if record.resource_type in allowed:
        return 1.0
    if modality(record.resource_type) == "mixed":
        return 0.6
    return 0.15


def score_resource(
    record: AssetRecord, graph: KnowledgeGraph, state: LearnerState
) -> ResourceRecommendation | None:
    if state.cost_preference == "free_only" and record.cost_type not in FREE_COSTS:
        return None
    if state.languages and record.language not in state.languages:
        return None
    if difficulty_delta(record.difficulty, _typical_difficulty(state)) > 2:
        return None
    if (
        state.weekly_minutes
        and record.estimated_duration
        and record.estimated_duration > state.weekly_minutes * 2
    ):
        return None
    goal = _goal_score(record, state)
    skill = _skill_score(record, state)
    career = _career_score(record, state)
    progress = _progress_score(record, graph, state)
    style = _style_score(record, state)
    total = 0.35 * goal + 0.25 * skill + 0.20 * career + 0.10 * progress + 0.10 * style
    quality_boost = max(0, min(record.quality_score, 100)) / 400
    total = min(1.0, total + quality_boost)
    reason = _reason(goal, skill, career, progress, style, record, state)
    return ResourceRecommendation(record, round(total, 4), reason)


def _typical_difficulty(state: LearnerState) -> str:
    if not state.mastery:
        return "beginner"
    mean = sum(state.mastery.values()) / len(state.mastery)
    if mean < 40:
        return "beginner"
    if mean < 70:
        return "intermediate"
    return "advanced"


def _reason(
    goal: float,
    skill: float,
    career: float,
    progress: float,
    style: float,
    record: AssetRecord,
    state: LearnerState,
) -> str:
    if skill >= 0.5 and state.weak_skills:
        matched = [item for item in state.weak_skills if item in record.skills]
        return f"Strengthens {', '.join(matched[:3])}."
    if goal >= 0.5 and state.goals:
        return f"On your path toward {state.goals[0].replace('-', ' ')}."
    role = career_role(state.career_goal)
    if career >= 0.4 and role is not None:
        return f"Used by {role.title}s."
    if progress >= 0.5:
        return "Prerequisites look in place for this resource."
    if style >= 0.8:
        return f"Matches a {state.learning_style.replace('_', '-')} style."
    return f"{record.resource_type.replace('_', ' ').title()} on {record.topic or record.category}."


def recommend_resources(
    records: list[AssetRecord],
    graph: KnowledgeGraph,
    state: LearnerState,
    limit: int = 8,
) -> list[ResourceRecommendation]:
    ranked: list[ResourceRecommendation] = []
    for record in records:
        item = score_resource(record, graph, state)
        if item is not None and item.score > 0.15:
            ranked.append(item)
    ranked.sort(key=lambda item: (-item.score, item.record.title))
    return ranked[:limit]
