"""Spaced-repetition scheduler.

SM-2 (the Anki variant) is the scheduler that ships. The protocol is the
extension point for FSRS. A wrong FSRS implementation would silently ruin
review intervals, so FSRS is not approximated here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ScheduleState:
    ease_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0


class Scheduler(Protocol):
    def review(self, state: ScheduleState, quality: int) -> ScheduleState:
        """Return the next schedule. Quality is an integer from 0 through 5."""


class SM2Scheduler:
    """Anki-compatible SM-2.

    Failed reviews (quality below 3) reset repetitions and the interval, and
    they do not change the ease factor. Successful reviews grow the interval
    1 day, then 6 days, then ceil(interval * ease), and then update ease.
    """

    def review(self, state: ScheduleState, quality: int) -> ScheduleState:
        if quality < 0 or quality > 5:
            raise ValueError("quality must be an integer from 0 to 5")
        ease = state.ease_factor
        interval = state.interval_days
        repetitions = state.repetitions
        if quality < 3:
            return ScheduleState(ease_factor=ease, interval_days=1, repetitions=0)
        if repetitions <= 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = max(1, math.ceil(interval * ease))
        ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ease < 1.3:
            ease = 1.3
        return ScheduleState(ease_factor=ease, interval_days=interval, repetitions=repetitions + 1)
