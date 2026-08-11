from __future__ import annotations

import logging

from fractalmesh.agents.core import Agent
from fractalmesh.agents.lifecycle import (
    pause_agent,
    resume_agent,
    spawn_agent,
    terminate_agent,
)
from fractalmesh.agents.registry import AgentRegistry


def test_agent_defaults() -> None:
    agent = Agent()
    assert agent.role == "general"
    assert agent.status == "active"
    assert agent.capabilities == []
    assert agent.agent_id


def test_registry_register_and_get(tmp_path) -> None:
    registry = AgentRegistry(f"sqlite:///{tmp_path / 'agents.db'}")
    agent = registry.register(Agent(role="worker", capabilities=["plan"]))
    fetched = registry.get(agent.agent_id)
    assert fetched is not None
    assert fetched.role == "worker"
    assert fetched.capabilities == ["plan"]


def test_registry_persists_to_sqlite(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'agents.db'}"
    registry = AgentRegistry(database_url)
    agent = registry.register(Agent(role="worker"))
    reloaded = AgentRegistry(database_url)
    assert reloaded.get(agent.agent_id) is not None


def test_registry_update_and_remove(tmp_path) -> None:
    registry = AgentRegistry(f"sqlite:///{tmp_path / 'agents.db'}")
    agent = registry.register(Agent())
    registry.update_status(agent.agent_id, "paused")
    assert registry.get(agent.agent_id).status == "paused"
    registry.remove(agent.agent_id)
    assert registry.get(agent.agent_id) is None


def test_lifecycle_logging_and_transitions(tmp_path, caplog) -> None:
    caplog.set_level(logging.INFO)
    registry = AgentRegistry(f"sqlite:///{tmp_path / 'agents.db'}")
    agent = spawn_agent("analyst", ["search"], {"x": 1}, registry)
    pause_agent(agent.agent_id, registry)
    resume_agent(agent.agent_id, registry)
    terminated = terminate_agent(agent.agent_id, registry)
    assert terminated is not None
    assert terminated.status == "terminated"
    assert "agent_event=spawn" in caplog.text
    assert "agent_event=terminate" in caplog.text
