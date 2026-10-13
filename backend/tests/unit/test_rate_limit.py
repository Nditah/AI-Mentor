from app.core.rate_limit import MemoryLimiter


def test_memory_limiter_blocks_after_the_limit_with_retry_after() -> None:
    limiter = MemoryLimiter()
    decisions = [limiter.hit("user:a:ai", 3, 60) for _ in range(4)]
    assert [item.allowed for item in decisions] == [True, True, True, False]
    assert decisions[2].remaining == 0
    headers = decisions[3].headers()
    assert int(headers["Retry-After"]) >= 1
    assert headers["RateLimit-Limit"] == "3"
    assert limiter.hit("user:b:ai", 3, 60).allowed
