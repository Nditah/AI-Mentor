"""XP, levels, streaks, and badge rules. Persistence lives in the service.

Values follow SRS GAM-002 and GAM-003. Every award has a source key, so the same
lesson, quiz, review, or analysis never pays twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

XP_PER_LEVEL = 250
DAILY_XP_CAP = 400
LESSON_XP = 40
REVIEW_XP = 5
CODE_XP = 25
ANALYSIS_XP = 10


@dataclass(frozen=True)
class XpRule:
    """`amount` is None when the caller computes it (quiz). `daily_limit` counts awards."""

    amount: int | None
    daily_limit: int | None = None


XP_RULES: dict[str, XpRule] = {
    "lesson": XpRule(LESSON_XP),
    "quiz": XpRule(None, daily_limit=10),
    "project": XpRule(CODE_XP),
    "review": XpRule(REVIEW_XP, daily_limit=20),
    "analysis": XpRule(ANALYSIS_XP, daily_limit=3),
    # Guided journey. Each source key pays once. Amounts for assessments and paths
    # are the authored reward, passed in by the caller.
    "knowledge_check": XpRule(5, daily_limit=20),
    "assessment": XpRule(None, daily_limit=10),
    "path": XpRule(None),
}


def learner_day(moment: datetime, timezone: str | None) -> date:
    """The learner's calendar day. An unknown zone falls back to UTC rather than failing."""

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    try:
        zone = ZoneInfo(timezone or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return moment.astimezone(zone).date()


def valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


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


def requested_xp(source_type: str, computed: int | None = None) -> int:
    rule = XP_RULES.get(source_type)
    if rule is None:
        raise ValueError(f"unknown xp source: {source_type}")
    if rule.amount is None:
        if computed is None or computed < 0:
            raise ValueError(f"{source_type} xp must be computed by the caller")
        return computed
    return rule.amount


def grant_for(source_type: str, requested: int, *, earned_today: int, awards_today: int) -> int:
    """XP actually granted after the per-event daily limit and the daily cap."""

    rule = XP_RULES.get(source_type)
    if rule is None:
        raise ValueError(f"unknown xp source: {source_type}")
    if rule.daily_limit is not None and awards_today >= rule.daily_limit:
        return 0
    return award_amount(requested, earned_today)


def quiz_xp(score_ratio: float) -> int:
    """`10 + round(40 × ratio)`, rounding half up (TestPlan C-11) instead of Python's half-even."""

    ratio = max(0.0, min(1.0, score_ratio))
    return 10 + int(40 * ratio + 0.5)


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
