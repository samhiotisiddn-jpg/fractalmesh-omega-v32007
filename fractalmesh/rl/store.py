from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def _sqlite_path(database_url: str) -> str:
    return database_url.replace("sqlite:///", "", 1)


class RLStore:
    def __init__(self, database_url: str = "sqlite:///fractalmesh.db") -> None:
        db_path = Path(_sqlite_path(database_url))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS rl_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                reward REAL NOT NULL,
                state_json TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rl_policy (
                action TEXT PRIMARY KEY,
                value_estimate REAL NOT NULL,
                count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rl_checkpoints (
                label TEXT PRIMARY KEY,
                policy_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def save_step(self, action: str, reward: float, state: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO rl_actions(action, reward, state_json, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (action, reward, json.dumps(state), datetime.utcnow().isoformat()),
        )
        self._conn.commit()

    def load_policy(self) -> dict[str, dict[str, float | int]]:
        rows = self._conn.execute("SELECT * FROM rl_policy").fetchall()
        return {
            row["action"]: {
                "value_estimate": row["value_estimate"],
                "count": row["count"],
            }
            for row in rows
        }

    def save_policy(self, policy: dict[str, dict[str, float | int]]) -> None:
        for action, values in policy.items():
            self._conn.execute(
                """
                INSERT INTO rl_policy(action, value_estimate, count)
                VALUES (?, ?, ?)
                ON CONFLICT(action) DO UPDATE SET
                    value_estimate=excluded.value_estimate,
                    count=excluded.count
                """,
                (
                    action,
                    float(values.get("value_estimate", 0.0)),
                    int(values.get("count", 0)),
                ),
            )
        self._conn.commit()

    def checkpoint(self, label: str) -> None:
        payload = json.dumps(self.load_policy())
        self._conn.execute(
            """
            INSERT INTO rl_checkpoints(label, policy_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(label) DO UPDATE SET
                policy_json=excluded.policy_json,
                created_at=excluded.created_at
            """,
            (label, payload, datetime.utcnow().isoformat()),
        )
        self._conn.commit()
