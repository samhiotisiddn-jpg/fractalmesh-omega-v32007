from __future__ import annotations

import json
from pathlib import Path

from perf_tracker.types import TrackerDocument, TrackerItem


def load_tracker(path: str | Path) -> TrackerDocument:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_items(document: TrackerDocument) -> list[TrackerItem]:
    return [item for section in document["sections"] for item in section["items"]]
