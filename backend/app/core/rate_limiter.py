import asyncio
import time

from app.core.config import get_settings


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def try_consume(self, amount: float = 1.0) -> tuple[bool, float]:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
            self.last_refill = now

            if self.tokens >= amount:
                self.tokens -= amount
                return True, 0.0

            deficit = amount - self.tokens
            retry_after = deficit / self.refill_per_sec if self.refill_per_sec > 0 else float("inf")
            return False, retry_after


_buckets: dict[str, TokenBucket] = {}
_buckets_lock = asyncio.Lock()


async def _get_bucket(key: str) -> TokenBucket:
    if key in _buckets:
        return _buckets[key]
    async with _buckets_lock:
        if key not in _buckets:
            settings = get_settings()
            _buckets[key] = TokenBucket(settings.rate_limit_capacity, settings.rate_limit_refill_per_sec)
        return _buckets[key]


async def check_rate_limit(key: str, amount: float = 1.0) -> tuple[bool, float]:
    """Returns (allowed, retry_after_seconds). One bucket per key (e.g. per
    username), created lazily with the configured capacity/refill rate."""
    bucket = await _get_bucket(key)
    return await bucket.try_consume(amount)
