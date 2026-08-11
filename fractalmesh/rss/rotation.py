from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RSSSource:
    url: str
    weight: float = 1.0
    last_fetched: datetime | None = None
    fail_count: int = 0
    ttl_seconds: int = 300


class SourcePool:
    def __init__(self) -> None:
        self.sources: dict[str, RSSSource] = {}
        self._seen_hashes: set[str] = set()

    def add_source(self, source: RSSSource) -> None:
        self.sources[source.url] = source

    def _is_ready(self, source: RSSSource, now: datetime) -> bool:
        if source.last_fetched is None:
            return True
        age = now - source.last_fetched
        backoff_seconds = max(source.ttl_seconds, (2**source.fail_count) * 30)
        return age >= timedelta(seconds=backoff_seconds)

    def next_source(self) -> RSSSource | None:
        now = datetime.utcnow()
        candidates = [source for source in self.sources.values() if self._is_ready(source, now)]
        if not candidates:
            return None
        weights = [max(source.weight, 0.01) for source in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def mark_success(self, url: str) -> None:
        source = self.sources[url]
        source.last_fetched = datetime.utcnow()
        source.fail_count = 0

    def mark_failure(self, url: str) -> None:
        source = self.sources[url]
        source.last_fetched = datetime.utcnow()
        source.fail_count += 1

    def is_duplicate(self, content_hash: str) -> bool:
        return content_hash in self._seen_hashes

    def record_seen(self, content_hash: str) -> None:
        self._seen_hashes.add(content_hash)
