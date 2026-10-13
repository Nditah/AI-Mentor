from datetime import date, timedelta

import pytest

from app.domain.gamification import (
    BadgeContext,
    award_amount,
    evaluate_badges,
    level_progress,
    next_streak,
    quiz_xp,
)


def test_level_progress_bands() -> None:
    assert level_progress(0) == (1, 0, 250)
    assert level_progress(250) == (2, 0, 250)
    assert level_progress(260) == (2, 10, 250)


def test_level_rejects_negative() -> None:
    with pytest.raises(ValueError):
        level_progress(-1)


def test_streak_starts_continues_and_resets() -> None:
    today = date(2026, 10, 13)
    assert next_streak(0, None, today) == 1
    assert next_streak(4, today, today) == 4
    assert next_streak(4, today - timedelta(days=1), today) == 5
    assert next_streak(4, today - timedelta(days=2), today) == 1


def test_daily_cap() -> None:
    assert award_amount(50, 380) == 20
    assert award_amount(50, 400) == 0
    assert quiz_xp(1) == 50
    assert quiz_xp(0) == 10


def test_badges() -> None:
    assert "first_steps" in evaluate_badges(BadgeContext(lessons_completed=1))
    assert "week_streak" in evaluate_badges(BadgeContext(streak_days=7))
    assert evaluate_badges(BadgeContext()) == frozenset()
