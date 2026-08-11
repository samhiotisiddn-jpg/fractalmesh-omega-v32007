from __future__ import annotations

from typing import Any, Literal, TypedDict

MemoryType = Literal["episodic", "semantic", "procedural"]


class MemoryRecord(TypedDict):
    record_id: str
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any]
    created_at: str
    embedding: list[float] | None
    importance: float
