from __future__ import annotations

import time


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = float(capacity)
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, n: int = 1) -> bool:
        self._refill()
        if self.tokens < n:
            return False
        self.tokens -= n
        return True


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, TokenBucket] = {}

    def _bucket_for(self, key: str) -> TokenBucket:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self.requests_per_minute,
                refill_rate=self.requests_per_minute / 60.0,
            )
        return self._buckets[key]

    def check(self, key: str) -> bool:
        return self._bucket_for(key).consume(1)

    def reset(self, key: str) -> None:
        self._buckets[key] = TokenBucket(
            capacity=self.requests_per_minute,
            refill_rate=self.requests_per_minute / 60.0,
        )
