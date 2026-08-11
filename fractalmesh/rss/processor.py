from __future__ import annotations

import hashlib
import html
import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.request import urlopen
from xml.etree import ElementTree

from .rotation import SourcePool

LOGGER = logging.getLogger(__name__)


class RSSProcessor:
    def __init__(
        self,
        source_pool: SourcePool,
        embed_fn: Callable[[str], list[float]],
        summarize_fn: Callable[[str], str] | None = None,
        opener: Callable[[str], Any] | None = None,
    ) -> None:
        self.source_pool = source_pool
        self.embed_fn = embed_fn
        self.summarize_fn = summarize_fn
        self._opener = opener or self._default_opener

    def _default_opener(self, url: str) -> str:
        with urlopen(url, timeout=10) as response:  # noqa: S310
            return response.read().decode("utf-8")

    def _extract_text(self, raw: str) -> str:
        stripped = re.sub(r"<[^>]+>", " ", raw)
        normalized = " ".join(stripped.split())
        return html.unescape(normalized)

    def fetch_and_process(self, url: str) -> list[dict[str, Any]]:
        try:
            payload = self._opener(url)
            root = ElementTree.fromstring(payload)
        except Exception:
            LOGGER.exception("Failed to fetch or parse RSS feed: %s", url)
            self.source_pool.mark_failure(url)
            return []
        events: list[dict[str, Any]] = []
        items = root.findall(".//item") or root.findall(".//entry")
        for item in items:
            title = (item.findtext("title") or "").strip()
            body = (
                item.findtext("description")
                or item.findtext("content")
                or item.findtext("summary")
                or ""
            )
            content = self._extract_text(body)
            content_hash = hashlib.sha256(
                f"{url}|{title}|{content}".encode()
            ).hexdigest()
            if self.source_pool.is_duplicate(content_hash):
                continue
            _ = self.embed_fn(content)
            summary = self.summarize_fn(content) if self.summarize_fn else content[:160]
            event = {
                "id": content_hash,
                "url": url,
                "title": title,
                "content": content,
                "summary": summary,
                "fetched_at": datetime.now(UTC).isoformat(),
            }
            self.source_pool.record_seen(content_hash)
            events.append(event)
        self.source_pool.mark_success(url)
        return events
