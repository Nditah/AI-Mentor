"""Fixed-window rate limits (SEC-035), with counters in Redis when running several instances.

Production requires `REDIS_URL`, so limits hold across replicas. Development and
tests fall back to a process-local counter.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int

    def headers(self) -> dict[str, str]:
        values = {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(self.remaining),
            "RateLimit-Reset": str(self.reset_seconds),
        }
        if not self.allowed:
            values["Retry-After"] = str(self.reset_seconds)
        return values


class Limiter(Protocol):
    def hit(self, key: str, limit: int, window_seconds: int) -> Decision: ...


def _window(now: float, window_seconds: int) -> tuple[int, int]:
    start = int(now // window_seconds) * window_seconds
    return start, max(1, math.ceil(start + window_seconds - now))


class MemoryLimiter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, int], int] = {}
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> Decision:
        start, reset = _window(time.time(), window_seconds)
        with self._lock:
            if len(self._counts) > 50_000:
                self._counts = {k: v for k, v in self._counts.items() if k[1] >= start}
            count = self._counts.get((key, start), 0) + 1
            self._counts[(key, start)] = count
        return Decision(count <= limit, limit, max(0, limit - count), reset)


class RedisLimiter:
    def __init__(self, url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)

    def hit(self, key: str, limit: int, window_seconds: int) -> Decision:
        start, reset = _window(time.time(), window_seconds)
        bucket = f"rl:{key}:{start}"
        try:
            pipe = self._client.pipeline()
            pipe.incr(bucket)
            pipe.expire(bucket, window_seconds + 5)
            count = int(pipe.execute()[0])
        except Exception:
            log.warning("rate limit store unavailable; allowing request", exc_info=True)
            return Decision(True, limit, limit, reset)
        return Decision(count <= limit, limit, max(0, limit - count), reset)


_limiter: Limiter | None = None


def limiter(redis_url: str | None) -> Limiter:
    global _limiter
    if _limiter is None:
        _limiter = RedisLimiter(redis_url) if redis_url else MemoryLimiter()
    return _limiter
