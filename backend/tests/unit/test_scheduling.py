import math

import pytest

from app.domain.scheduling import ScheduleState, SM2Scheduler


def test_successful_reviews_follow_anki_sm2() -> None:
    scheduler = SM2Scheduler()
    first = scheduler.review(ScheduleState(), 5)
    assert first.repetitions == 1
    assert first.interval_days == 1
    assert first.ease_factor == pytest.approx(2.6)

    second = scheduler.review(first, 5)
    assert second.repetitions == 2
    assert second.interval_days == 6
    assert second.ease_factor == pytest.approx(2.7)

    third = scheduler.review(second, 5)
    assert third.interval_days == math.ceil(6 * second.ease_factor)
    assert third.repetitions == 3


def test_failed_review_resets_without_changing_ease() -> None:
    scheduler = SM2Scheduler()
    state = ScheduleState(ease_factor=2.4, interval_days=12, repetitions=4)
    failed = scheduler.review(state, 1)
    assert failed.repetitions == 0
    assert failed.interval_days == 1
    assert failed.ease_factor == 2.4


def test_ease_floor_and_quality_bounds() -> None:
    scheduler = SM2Scheduler()
    hard = scheduler.review(ScheduleState(ease_factor=1.3, repetitions=2, interval_days=6), 3)
    assert hard.ease_factor == 1.3
    with pytest.raises(ValueError):
        scheduler.review(ScheduleState(), 6)
