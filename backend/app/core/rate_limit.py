"""Process-local limiter. Use a shared store before running more than one instance."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: float = 60) -> bool:
        now = time.monotonic()
        with self._lock:
            fresh = [stamp for stamp in self._hits[key] if now - stamp < window_seconds]
            if len(fresh) >= limit:
                self._hits[key] = fresh
                return False
            fresh.append(now)
            self._hits[key] = fresh
            return True
