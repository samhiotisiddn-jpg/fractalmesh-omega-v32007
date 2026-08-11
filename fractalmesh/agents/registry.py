from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .core import Agent, AgentStatus


def _sqlite_path(database_url: str) -> str:
    return database_url.replace("sqlite:///", "", 1)


class AgentRegistry:
    def __init__(self, database_url: str | None = None) -> None:
        self._agents: dict[str, Agent] = {}
        self._health: dict[str, dict[str, str]] = {}
        self._conn: sqlite3.Connection | None = None
        if database_url:
            db_path = Path(_sqlite_path(database_url))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(db_path)
            self._conn.row_factory = sqlite3.Row
            self._ensure_schema()
            self._load_existing()

    def _ensure_schema(self) -> None:
        if self._conn is None:
            return
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                config TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _load_existing(self) -> None:
        if self._conn is None:
            return
        rows = self._conn.execute("SELECT * FROM agents").fetchall()
        for row in rows:
            agent = self._row_to_agent(row)
            self._agents[agent.agent_id] = agent
            self._touch_health(agent.agent_id, agent.status)

    def _row_to_agent(self, row: sqlite3.Row) -> Agent:
        return Agent(
            agent_id=row["agent_id"],
            role=row["role"],
            capabilities=json.loads(row["capabilities"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            config=json.loads(row["config"]),
        )

    def _persist(self, agent: Agent) -> None:
        if self._conn is None:
            return
        self._conn.execute(
            """
            INSERT INTO agents(agent_id, role, capabilities, created_at, status, config)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                role=excluded.role,
                capabilities=excluded.capabilities,
                created_at=excluded.created_at,
                status=excluded.status,
                config=excluded.config
            """,
            (
                agent.agent_id,
                agent.role,
                json.dumps(agent.capabilities),
                agent.created_at.isoformat(),
                agent.status,
                json.dumps(agent.config),
            ),
        )
        self._conn.commit()

    def _touch_health(self, agent_id: str, status: AgentStatus) -> None:
        self._health[agent_id] = {
            "last_seen": datetime.utcnow().isoformat(),
            "status": status,
        }

    def register(self, agent: Agent) -> Agent:
        self._agents[agent.agent_id] = agent
        self._persist(agent)
        self._touch_health(agent.agent_id, agent.status)
        return agent

    def get(self, agent_id: str) -> Agent | None:
        agent = self._agents.get(agent_id)
        if agent is not None or self._conn is None:
            return agent
        row = self._conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        if row is None:
            return None
        agent = self._row_to_agent(row)
        self._agents[agent.agent_id] = agent
        self._touch_health(agent.agent_id, agent.status)
        return agent

    def list_agents(self) -> list[Agent]:
        return list(self._agents.values())

    def update_status(self, agent_id: str, status: AgentStatus) -> Agent | None:
        agent = self.get(agent_id)
        if agent is None:
            return None
        agent.status = status
        self._persist(agent)
        self._touch_health(agent_id, status)
        return agent

    def remove(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)
        self._health.pop(agent_id, None)
        if self._conn is not None:
            self._conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            self._conn.commit()

    def get_health(self, agent_id: str) -> dict[str, str] | None:
        return self._health.get(agent_id)
