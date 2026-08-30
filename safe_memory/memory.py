"""Local transactional memory store with tiering, retrieval, and decay.

Implemented against stdlib + sqlite3. No third-party packages required for the
core store. Optional semantic search requires `sqlite-vec` or Chroma.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class MemoryTier(Enum):
    SENSORY = "sensory"
    SHORT_TERM = "short_term"
    LONG_TERM_EXPLICIT = "long_term_explicit"
    LONG_TERM_IMPLICIT = "long_term_implicit"


@dataclass(frozen=True, slots=True)
class Memory:
    id: str
    content: str
    tier: MemoryTier
    created_at: datetime
    last_accessed_at: datetime
    confidence: float
    tokens: int
    meta: dict[str, Any]


class SuperLocalMemory:
    """SQLite-backed tiered memory store.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file. ``:memory:`` works for tests.
    stm_ttl_seconds:
        Short-term memories decay to ``long_term_implicit`` after this many
        seconds without access.
    """

    def __init__(self, db_path: str = "./slm.db", stm_ttl_seconds: int = 24 * 3600):
        self.db_path = db_path
        self.stm_ttl = timedelta(seconds=stm_ttl_seconds)
        self._init_schema()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    tokens INTEGER NOT NULL,
                    meta TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_tier_confidence
                ON memories(tier, confidence DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_accessed
                ON memories(last_accessed_at)
                """
            )
            conn.commit()

    def add(
        self,
        content: str,
        tier: MemoryTier,
        confidence: float = 0.5,
        tokens: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Memory:
        """Atomically insert a memory.

        ``tokens`` is estimated from whitespace-separated words when not given.
        """
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence must be in [0, 1]")
        now = datetime.now(timezone.utc)
        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            tier=tier,
            created_at=now,
            last_accessed_at=now,
            confidence=confidence,
            tokens=tokens or len(content.split()),
            meta=meta or {},
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (id, content, tier, created_at,
                    last_accessed_at, confidence, tokens, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.content,
                    memory.tier.value,
                    memory.created_at.isoformat(),
                    memory.last_accessed_at.isoformat(),
                    memory.confidence,
                    memory.tokens,
                    json.dumps(memory.meta),
                ),
            )
            conn.commit()
        return memory

    def get(self, memory_id: str) -> Memory | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_memory(row)

    def search(
        self,
        tier: MemoryTier | None = None,
        keyword: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 20,
    ) -> list[Memory]:
        """Keyword and tier filtered retrieval.

        This is the baseline channel. Semantic/vector retrieval can be layered
        on top by callers that load an embedding model locally.
        """
        query = "SELECT * FROM memories WHERE confidence >= ?"
        params: list[Any] = [min_confidence]
        if tier is not None:
            query += " AND tier = ?"
            params.append(tier.value)
        if keyword:
            query += " AND content LIKE ?"
            params.append(f"%{keyword}%")
        query += " ORDER BY confidence DESC, last_accessed_at DESC LIMIT ?"
        params.append(limit)

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def decay_and_quantize(self) -> dict[str, int]:
        """Move stale short-term memories to implicit LTM and drop junk."""
        cutoff = (datetime.now(timezone.utc) - self.stm_ttl).isoformat()
        with self._connection() as conn:
            moved = conn.execute(
                """
                UPDATE memories
                SET tier = ?, confidence = confidence * 0.9
                WHERE tier = ? AND last_accessed_at < ?
                """,
                (MemoryTier.LONG_TERM_IMPLICIT.value, MemoryTier.SHORT_TERM.value, cutoff),
            ).rowcount

            # Very low-confidence sensory data can be forgotten entirely.
            forgotten = conn.execute(
                """
                DELETE FROM memories
                WHERE tier = ? AND confidence < 0.05
                """,
                (MemoryTier.SENSORY.value,),
            ).rowcount
            conn.commit()
        return {"moved_to_implicit": moved, "forgotten": forgotten}

    def get_soft_prompt(self, budget_tokens: int = 1500) -> str:
        """Build a natural-language soft prompt from durable memories."""
        rows = self.search(
            tier=MemoryTier.LONG_TERM_EXPLICIT,
            min_confidence=0.6,
            limit=100,
        ) + self.search(
            tier=MemoryTier.LONG_TERM_IMPLICIT,
            min_confidence=0.4,
            limit=100,
        )
        rows.sort(key=lambda m: (m.confidence, m.last_accessed_at), reverse=True)
        chunks, used = [], 0
        for memory in rows:
            if used + memory.tokens > budget_tokens:
                break
            chunks.append(f"- {memory.content}")
            used += memory.tokens
        return "\n".join(chunks)

    def touch(self, memory_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            conn.execute(
                "UPDATE memories SET last_accessed_at = ? WHERE id = ?",
                (now, memory_id),
            )
            conn.commit()

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            content=row["content"],
            tier=MemoryTier(row["tier"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed_at=datetime.fromisoformat(row["last_accessed_at"]),
            confidence=row["confidence"],
            tokens=row["tokens"],
            meta=json.loads(row["meta"]),
        )
