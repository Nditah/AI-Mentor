"""Mastery is a read model computed from evidence, then stored for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass

STRENGTH_AT = 75
GAP_BELOW = 60


@dataclass(frozen=True)
class Evidence:
    quiz_scores: tuple[float, ...] = ()
    lessons_completed: int = 0
    lessons_available: int = 0
    projects_passed: int = 0
    projects_attempted: int = 0
    recall: float | None = None


def band(score: int) -> str:
    if score >= STRENGTH_AT:
        return "strength"
    if score >= GAP_BELOW:
        return "developing"
    if score > 0:
        return "gap"
    return "unstarted"


def _ratio(done: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, done / total))


def score_evidence(evidence: Evidence) -> int:
    """Renormalize over the evidence we actually have.

    Lessons count once the learner has any activity and the concept has a
    lesson, so a single perfect quiz cannot read as full mastery. Projects
    count only after an attempt, so an untouched lab does not punish the score.
    """

    parts: list[tuple[float, float]] = []
    if evidence.quiz_scores:
        mean = sum(evidence.quiz_scores) / len(evidence.quiz_scores)
        parts.append((0.45, max(0.0, min(1.0, mean))))
    engaged = bool(
        evidence.quiz_scores or evidence.lessons_completed or evidence.projects_attempted
    )
    if engaged and evidence.lessons_available > 0:
        parts.append((0.25, _ratio(evidence.lessons_completed, evidence.lessons_available)))
    if evidence.projects_attempted > 0:
        parts.append((0.20, _ratio(evidence.projects_passed, evidence.projects_attempted)))
    if evidence.recall is not None:
        parts.append((0.10, max(0.0, min(1.0, evidence.recall))))
    if not parts:
        return 0
    weight = sum(weight for weight, _ in parts)
    value = sum(weight * score for weight, score in parts) / weight
    return int(round(max(0.0, min(1.0, value)) * 100))
