from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def _sqlite_path(database_url: str) -> str:
    return database_url.replace("sqlite:///", "", 1)


class MCPToolRegistry:
    def __init__(self, database_url: str = "sqlite:///fractalmesh.db") -> None:
        db_path = Path(_sqlite_path(database_url))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_tools (
                tool_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                server_name TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def register_tool(self, tool: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO mcp_tools(tool_id, name, description, server_name, schema_json, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tool_id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                server_name=excluded.server_name,
                schema_json=excluded.schema_json,
                last_seen=excluded.last_seen
            """,
            (
                tool["tool_id"],
                tool["name"],
                tool.get("description", ""),
                tool["server_name"],
                json.dumps(tool.get("schema", {})),
                datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def lookup(self, name: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM mcp_tools WHERE name = ? ORDER BY last_seen DESC LIMIT 1",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return {
            "tool_id": row["tool_id"],
            "name": row["name"],
            "description": row["description"],
            "server_name": row["server_name"],
            "schema": json.loads(row["schema_json"]),
            "last_seen": row["last_seen"],
        }

    def list_tools(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM mcp_tools ORDER BY name").fetchall()
        return [
            {
                "tool_id": row["tool_id"],
                "name": row["name"],
                "description": row["description"],
                "server_name": row["server_name"],
                "schema": json.loads(row["schema_json"]),
                "last_seen": row["last_seen"],
            }
            for row in rows
        ]
