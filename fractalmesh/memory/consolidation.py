from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Callable

from .base import MemoryRecord
from .sqlite_store import SQLiteMemoryStore


def consolidate(
    store: SQLiteMemoryStore,
    threshold: int,
    summarize_fn: Callable[[list[str]], str],
) -> int:
    rows = store.conn.execute(
        "SELECT * FROM memories WHERE memory_type = 'episodic' ORDER BY created_at"
    ).fetchall()
    records = [store._row_to_record(row) for row in rows]
    pending = [record for record in records if not record["metadata"].get("consolidated")]
    if len(pending) <= threshold:
        return 0
    grouped: dict[str, list[MemoryRecord]] = defaultdict(list)
    for record in pending:
        grouped[record["created_at"][:10]].append(record)
    consolidated = 0
    for day, batch in grouped.items():
        summary = summarize_fn([record["content"] for record in batch])
        semantic_record: MemoryRecord = {
            "record_id": str(uuid.uuid4()),
            "memory_type": "semantic",
            "content": summary,
            "metadata": {"source_date": day, "source_ids": [r["record_id"] for r in batch]},
            "created_at": f"{day}T23:59:59",
            "embedding": None,
            "importance": max(record["importance"] for record in batch),
        }
        store.store(semantic_record)
        for record in batch:
            updated = dict(record)
            metadata = dict(record["metadata"])
            metadata["consolidated"] = True
            updated["metadata"] = metadata
            store.store(updated)
            consolidated += 1
    return consolidated
