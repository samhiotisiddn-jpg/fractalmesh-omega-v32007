from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from perf_tracker.config import get_max_json_bytes
from perf_tracker.errors import ValidationError
from perf_tracker.types import TrackerDocument, TrackerItem

DEFAULT_MAX_JSON_DEPTH = 64
DEFAULT_MAX_JSON_NODES = 200_000


def resolve_repo_path(path: str | Path, repo_root: str | Path) -> Path:
    raw_path = Path(path)
    if ".." in raw_path.parts:
        raise ValidationError(f"Path traversal is not allowed: {path}")

    if raw_path.is_absolute():
        return raw_path.resolve()

    root = Path(repo_root).resolve()
    resolved = (root / raw_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"Relative path escapes repository root: {path}") from exc
    return resolved


def _guard_json_payload(value: Any, *, max_depth: int, max_nodes: int) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    node_count = 0

    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > max_nodes:
            raise ValidationError(f"JSON payload exceeds node limit ({max_nodes})")
        if depth > max_depth:
            raise ValidationError(f"JSON payload exceeds nesting limit ({max_depth})")
        if isinstance(node, dict):
            stack.extend((entry, depth + 1) for entry in node.values())
        elif isinstance(node, list):
            stack.extend((entry, depth + 1) for entry in node)


def load_tracker(
    path: str | Path,
    *,
    max_bytes: int | None = None,
    max_depth: int = DEFAULT_MAX_JSON_DEPTH,
    max_nodes: int = DEFAULT_MAX_JSON_NODES,
) -> TrackerDocument:
    tracker_path = Path(path)
    size_limit = get_max_json_bytes() if max_bytes is None else max_bytes
    if size_limit <= 0:
        raise ValidationError("max_bytes must be a positive integer")
    if tracker_path.stat().st_size > size_limit:
        raise ValidationError(f"Tracker JSON exceeds maximum allowed size ({size_limit} bytes)")

    with tracker_path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)

    _guard_json_payload(document, max_depth=max_depth, max_nodes=max_nodes)
    if not isinstance(document, dict):
        raise ValidationError("tracker document must be a JSON object")
    return cast(TrackerDocument, document)


def safe_write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def list_items(document: TrackerDocument) -> list[TrackerItem]:
    return [item for section in document["sections"] for item in section["items"]]
