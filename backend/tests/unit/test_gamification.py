from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.gamification import (
    BadgeContext,
    award_amount,
    evaluate_badges,
    grant_for,
    learner_day,
    level_progress,
    next_streak,
    quiz_xp,
    requested_xp,
    valid_timezone,
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


def test_quiz_xp_rounds_half_up() -> None:
    assert quiz_xp(0.3125) == 23
    assert quiz_xp(2) == 50
    assert quiz_xp(-1) == 10


def test_requested_xp_follows_the_srs_table() -> None:
    assert requested_xp("lesson") == 40
    assert requested_xp("project") == 25
    assert requested_xp("review") == 5
    assert requested_xp("analysis") == 10
    assert requested_xp("quiz", 30) == 30
    with pytest.raises(ValueError):
        requested_xp("quiz")
    with pytest.raises(ValueError):
        requested_xp("chat")


def test_per_event_daily_limits_and_cap() -> None:
    assert grant_for("analysis", 10, earned_today=0, awards_today=2) == 10
    assert grant_for("analysis", 10, earned_today=0, awards_today=3) == 0
    assert grant_for("review", 5, earned_today=0, awards_today=20) == 0
    assert grant_for("quiz", 50, earned_today=0, awards_today=10) == 0
    assert grant_for("lesson", 40, earned_today=390, awards_today=50) == 10
    with pytest.raises(ValueError):
        grant_for("unknown", 1, earned_today=0, awards_today=0)


def test_learner_day_uses_the_learner_timezone() -> None:
    late_utc = datetime(2026, 10, 13, 23, 30, tzinfo=UTC)
    assert learner_day(late_utc, "UTC") == date(2026, 10, 13)
    assert learner_day(late_utc, "Africa/Lagos") == date(2026, 10, 14)
    assert learner_day(late_utc, "America/Mexico_City") == date(2026, 10, 13)
    assert learner_day(datetime(2026, 10, 13, 23, 30), "Not/AZone") == date(2026, 10, 13)
    assert valid_timezone("Europe/Paris")
    assert not valid_timezone("Mars/Base")


def test_badges() -> None:
    assert "first_steps" in evaluate_badges(BadgeContext(lessons_completed=1))
    assert "week_streak" in evaluate_badges(BadgeContext(streak_days=7))
    assert evaluate_badges(BadgeContext()) == frozenset()
