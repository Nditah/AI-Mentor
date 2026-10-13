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


DAILY_XP = 25
STREAK_FREEZE_MAX = 2
STREAK_MARKS = (7, 30)
STREAK_MILESTONES = (1, 7, 30, 100, 365)

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
    "daily": XpRule(DAILY_XP, daily_limit=1),
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


def advance_streak(
    previous: int, last_active: date | None, today: date, freezes: int
) -> tuple[int, int, bool]:
    """Advance the streak, spending one freeze only for a single missed calendar day.

    A freeze is a grace day, not a purchase and not a punishment. Missing two or more
    days starts a new run and leaves unused freezes in place. The personal-best streak
    is stored separately by the service.
    """

    if last_active == today:
        return max(previous, 1), freezes, False
    if last_active is None:
        return 1, freezes, False
    if last_active == today - timedelta(days=1):
        return previous + 1, freezes, False
    if last_active == today - timedelta(days=2) and freezes > 0:
        return previous + 1, freezes - 1, True
    return 1, freezes, False


def earned_freezes(previous_streak: int, new_streak: int, current: int) -> int:
    """Grant a freeze when a 7-day or 30-day mark is crossed, up to STREAK_FREEZE_MAX."""

    gained = sum(1 for mark in STREAK_MARKS if previous_streak < mark <= new_streak)
    return min(STREAK_FREEZE_MAX, current + gained)


def streak_bonus_percent(streak: int) -> int:
    """Modest lesson XP bonus. Never a slot machine; still subject to the daily cap."""

    if streak >= 100:
        return 15
    if streak >= 30:
        return 10
    if streak >= 7:
        return 5
    return 0


def streak_bonus_xp(base: int, streak: int) -> int:
    return (base * streak_bonus_percent(streak) + 99) // 100


def mentor_stage(level: int) -> dict[str, str]:
    """The mentor silhouette grows with the learner. It is cosmetic, not a paywall."""

    if level >= 40:
        return {"id": "grandmaster", "name": "Grandmaster Mentor"}
    if level >= 20:
        return {"id": "research", "name": "Research Mentor"}
    if level >= 10:
        return {"id": "expert", "name": "Expert Mentor"}
    if level >= 5:
        return {"id": "practitioner", "name": "Practitioner Mentor"}
    return {"id": "novice", "name": "Novice Mentor"}


def card_tier(score: int) -> str | None:
    """A skill card appears only after demonstrated mastery, never as a drop."""

    if score >= 90:
        return "gold"
    if score >= 75:
        return "silver"
    if score >= 60:
        return "bronze"
    return None


def near_win(
    *,
    remaining_lessons: int | None = None,
    remaining_concepts: int | None = None,
    next_unlock: str | None = None,
    percent: int | None = None,
) -> str:
    """Goal-gradient copy. Honest remaining work, never fake scarcity."""

    if remaining_lessons == 1:
        return "One lesson remaining on this path."
    if remaining_lessons is not None and 1 < remaining_lessons <= 3:
        return f"Only {remaining_lessons} lessons remaining."
    if remaining_concepts == 1 and next_unlock:
        return f"One concept until you unlock {next_unlock}."
    if remaining_concepts is not None and 1 < remaining_concepts <= 3 and next_unlock:
        return f"{remaining_concepts} concepts until you unlock {next_unlock}."
    if next_unlock and percent is not None and percent >= 80:
        return f"Complete this module to unlock {next_unlock}."
    if percent is not None and percent > 0:
        return f"{percent}% complete."
    return "Start a lesson to open today's run."


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
    level: int = 1
    path_slugs: frozenset[str] = frozenset()


def evaluate_badges(context: BadgeContext) -> frozenset[str]:
    earned: set[str] = set()
    if context.lessons_completed >= 1:
        earned.add("first_steps")
    if context.streak_days >= 3:
        earned.add("streak_3")
    if context.streak_days >= 7:
        earned.add("week_streak")
    if context.streak_days >= 30:
        earned.add("streak_30")
    if context.streak_days >= 100:
        earned.add("streak_100")
    if context.streak_days >= 365:
        earned.add("streak_365")
    if context.perfect_quiz:
        earned.add("perfect_quiz")
    if context.max_mastery >= 80:
        earned.add("mastery")
    if context.analyses >= 1:
        earned.add("reviewer")
    if context.code_passes >= 1:
        earned.add("shipped_code")
    if "rl-foundations" in context.path_slugs:
        earned.add("rl_pioneer")
    if context.level >= 10:
        earned.add("ai_apprentice")
    if context.level >= 20:
        earned.add("grandmaster_architect")
    return frozenset(earned)


@dataclass(frozen=True)
class TitleDef:
    slug: str
    name: str
    min_level: int
    description: str


TITLES: tuple[TitleDef, ...] = (
    TitleDef("ai_apprentice", "AI Apprentice", 1, "Opened the first lesson."),
    TitleDef("data_scientist", "Data Scientist", 5, "Reached level 5 through scored practice."),
    TitleDef(
        "ml_engineer",
        "Machine Learning Engineer",
        10,
        "Held a double-digit level from lessons, quizzes, and labs.",
    ),
    TitleDef(
        "cv_specialist",
        "Computer Vision Specialist",
        12,
        "Reached level 12. A specialist title, not a vendor certificate.",
    ),
    TitleDef("robotics_engineer", "Robotics Engineer", 15, "Reached level 15."),
    TitleDef(
        "research_fellow",
        "Research Fellow",
        20,
        "Reached level 20 with research or lab evidence.",
    ),
    TitleDef(
        "professor_of_ai",
        "Professor of AI",
        30,
        "A recognition title, not an academic appointment.",
    ),
    TitleDef(
        "grandmaster_architect",
        "Grandmaster AI Architect",
        40,
        "The highest recognition title. Not a degree.",
    ),
)


def evaluate_titles(*, level: int, badges: frozenset[str]) -> frozenset[str]:
    earned = {title.slug for title in TITLES if level >= title.min_level}
    if "rl_pioneer" in badges:
        earned.add("ml_engineer")
    return frozenset(earned)


def welcome_back(previous_best: int, reset: bool) -> str | None:
    if reset and previous_best >= 7:
        return (
            f"Welcome back. Your {previous_best}-day run is still your personal best. "
            "Today starts a new one — nothing is taken away."
        )
    return None
