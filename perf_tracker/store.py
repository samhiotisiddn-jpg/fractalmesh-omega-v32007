from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tracker_documents (
                id TEXT PRIMARY KEY,
                source_issue TEXT NOT NULL,
                source_title TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def upsert_document(
    db_path: str | Path,
    *,
    doc_id: str,
    source_issue: str,
    source_title: str,
    data: dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(data)
    with _connect(db_path) as connection:
        connection.execute("BEGIN")
        connection.execute(
            """
            INSERT INTO tracker_documents (id, source_issue, source_title, data_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_issue = excluded.source_issue,
                source_title = excluded.source_title,
                data_json = excluded.data_json,
                updated_at = excluded.updated_at
            """,
            (doc_id, source_issue, source_title, payload, now, now),
        )
        connection.commit()


def get_document(db_path: str | Path, doc_id: str) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, source_issue, source_title, data_json, created_at, updated_at
            FROM tracker_documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "source_issue": row["source_issue"],
        "source_title": row["source_title"],
        "data": json.loads(row["data_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_documents(db_path: str | Path) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, source_issue, source_title, data_json, created_at, updated_at
            FROM tracker_documents
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "source_issue": row["source_issue"],
            "source_title": row["source_title"],
            "data": json.loads(row["data_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def prune_old_documents(db_path: str | Path, days: int) -> int:
    if days < 0:
        raise ValueError("days must be >= 0")
    with _connect(db_path) as connection:
        result = connection.execute(
            """
            DELETE FROM tracker_documents
            WHERE updated_at < datetime('now', ?)
            """,
            (f"-{days} days",),
        )
        connection.commit()
    return int(result.rowcount)
