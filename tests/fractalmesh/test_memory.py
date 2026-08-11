from __future__ import annotations

from fractalmesh.memory.base import MemoryRecord
from fractalmesh.memory.consolidation import consolidate
from fractalmesh.memory.sqlite_store import SQLiteMemoryStore


def _record(record_id: str, memory_type: str, content: str, created_at: str) -> MemoryRecord:
    return {
        "record_id": record_id,
        "memory_type": memory_type,
        "content": content,
        "metadata": {},
        "created_at": created_at,
        "embedding": [0.1, 0.2],
        "importance": 0.8,
    }


def test_memory_record_shape() -> None:
    record = _record("1", "episodic", "remember this", "2026-01-01T00:00:00")
    assert record["record_id"] == "1"
    assert record["embedding"] == [0.1, 0.2]


def test_sqlite_memory_store_crud(tmp_path) -> None:
    store = SQLiteMemoryStore(f"sqlite:///{tmp_path / 'memory.db'}")
    record = _record("1", "episodic", "remember this", "2026-01-01T00:00:00")
    store.store(record)
    fetched = store.get("1")
    assert fetched is not None
    assert fetched["content"] == "remember this"


def test_sqlite_memory_store_search_and_count(tmp_path) -> None:
    store = SQLiteMemoryStore(f"sqlite:///{tmp_path / 'memory.db'}")
    store.store(_record("1", "episodic", "alpha memory", "2026-01-01T00:00:00"))
    store.store(_record("2", "semantic", "beta memory", "2026-01-01T01:00:00"))
    results = store.search("alpha")
    assert len(results) == 1
    assert store.count() == 2


def test_sqlite_memory_store_delete(tmp_path) -> None:
    store = SQLiteMemoryStore(f"sqlite:///{tmp_path / 'memory.db'}")
    store.store(_record("1", "episodic", "discard me", "2026-01-01T00:00:00"))
    store.delete("1")
    assert store.get("1") is None


def test_consolidation_creates_semantic_summary(tmp_path) -> None:
    store = SQLiteMemoryStore(f"sqlite:///{tmp_path / 'memory.db'}")
    store.store(_record("1", "episodic", "first event", "2026-01-01T08:00:00"))
    store.store(_record("2", "episodic", "second event", "2026-01-01T09:00:00"))
    total = consolidate(store, threshold=1, summarize_fn=lambda batch: " | ".join(batch))
    semantic = store.search("first", memory_type="semantic")
    updated = store.get("1")
    assert total == 2
    assert semantic
    assert updated is not None
    assert updated["metadata"]["consolidated"] is True
