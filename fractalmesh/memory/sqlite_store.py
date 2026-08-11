from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .base import MemoryRecord, MemoryType


def _sqlite_path(database_url: str) -> str:
    return database_url.replace("sqlite:///", "", 1)


class SQLiteMemoryStore:
    def __init__(self, database_url: str = "sqlite:///fractalmesh.db") -> None:
        db_path = Path(_sqlite_path(database_url))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.fts_enabled = False
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                record_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                embedding_json TEXT,
                importance REAL NOT NULL
            )
            """
        )
        try:
            self.conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                USING fts5(record_id UNINDEXED, content)
                """
            )
            self.fts_enabled = True
        except sqlite3.OperationalError:
            self.fts_enabled = False
        self.conn.commit()

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        embedding_json = row["embedding_json"]
        return {
            "record_id": row["record_id"],
            "memory_type": row["memory_type"],
            "content": row["content"],
            "metadata": json.loads(row["metadata_json"]),
            "created_at": row["created_at"],
            "embedding": json.loads(embedding_json) if embedding_json else None,
            "importance": row["importance"],
        }

    def store(self, record: MemoryRecord) -> None:
        self.conn.execute(
            """
            INSERT INTO memories(
                record_id,
                memory_type,
                content,
                metadata_json,
                created_at,
                embedding_json,
                importance
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                memory_type=excluded.memory_type,
                content=excluded.content,
                metadata_json=excluded.metadata_json,
                created_at=excluded.created_at,
                embedding_json=excluded.embedding_json,
                importance=excluded.importance
            """,
            (
                record["record_id"],
                record["memory_type"],
                record["content"],
                json.dumps(record["metadata"]),
                record["created_at"],
                json.dumps(record["embedding"]),
                record["importance"],
            ),
        )
        if self.fts_enabled:
            self.conn.execute(
                "DELETE FROM memory_fts WHERE record_id = ?",
                (record["record_id"],),
            )
            self.conn.execute(
                "INSERT INTO memory_fts(record_id, content) VALUES (?, ?)",
                (record["record_id"], record["content"]),
            )
        self.conn.commit()

    def get(self, record_id: str) -> MemoryRecord | None:
        row = self.conn.execute(
            "SELECT * FROM memories WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return self._row_to_record(row) if row else None

    def search(
        self,
        query: str,
        memory_type: MemoryType | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        params: list[object] = []
        if self.fts_enabled and query.strip():
            sql = (
                "SELECT m.* FROM memories m JOIN memory_fts f ON m.record_id = f.record_id "
                "WHERE f.content MATCH ?"
            )
            params.append(query)
        else:
            sql = "SELECT * FROM memories WHERE content LIKE ?"
            params.append(f"%{query}%")
        if memory_type is not None:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def delete(self, record_id: str) -> None:
        self.conn.execute("DELETE FROM memories WHERE record_id = ?", (record_id,))
        if self.fts_enabled:
            self.conn.execute("DELETE FROM memory_fts WHERE record_id = ?", (record_id,))
        self.conn.commit()

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS total FROM memories").fetchone()
        return int(row["total"])
