"""XP, levels, streaks, and badge rules. Persistence lives in the service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

XP_PER_LEVEL = 250
DAILY_XP_CAP = 400
LESSON_XP = 40
REVIEW_XP = 5
CODE_XP = 25


def level_progress(xp: int) -> tuple[int, int, int]:
    if xp < 0:
        raise ValueError("xp cannot be negative")
    level = 1 + xp // XP_PER_LEVEL
    return level, xp % XP_PER_LEVEL, XP_PER_LEVEL


def next_streak(previous: int, last_active: date | None, today: date) -> int:
    if last_active == today:
        return max(previous, 1)
    if last_active == today - timedelta(days=1):
        return previous + 1
    return 1


def award_amount(requested: int, earned_today: int, cap: int = DAILY_XP_CAP) -> int:
    if requested < 0 or earned_today < 0:
        raise ValueError("xp amounts cannot be negative")
    return max(0, min(requested, cap - earned_today))


def quiz_xp(score_ratio: float) -> int:
    ratio = max(0.0, min(1.0, score_ratio))
    return 10 + round(40 * ratio)


@dataclass(frozen=True)
class BadgeContext:
    lessons_completed: int = 0
    streak_days: int = 0
    perfect_quiz: bool = False
    max_mastery: int = 0
    analyses: int = 0
    code_passes: int = 0


def evaluate_badges(context: BadgeContext) -> frozenset[str]:
    earned: set[str] = set()
    if context.lessons_completed >= 1:
        earned.add("first_steps")
    if context.streak_days >= 3:
        earned.add("streak_3")
    if context.streak_days >= 7:
        earned.add("week_streak")
    if context.perfect_quiz:
        earned.add("perfect_quiz")
    if context.max_mastery >= 80:
        earned.add("mastery")
    if context.analyses >= 1:
        earned.add("reviewer")
    if context.code_passes >= 1:
        earned.add("shipped_code")
    return frozenset(earned)
