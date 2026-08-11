from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .core import Agent
from .registry import AgentRegistry

LOGGER = logging.getLogger(__name__)


def _log_event(event: str, agent_id: str) -> None:
    timestamp = datetime.now(UTC).isoformat()
    LOGGER.info("agent_event=%s agent_id=%s timestamp=%s", event, agent_id, timestamp)


def spawn_agent(
    role: str,
    capabilities: list[str],
    config: dict[str, Any],
    registry: AgentRegistry,
) -> Agent:
    agent = Agent(role=role, capabilities=capabilities, config=config)
    registry.register(agent)
    _log_event("spawn", agent.agent_id)
    return agent


def pause_agent(agent_id: str, registry: AgentRegistry) -> Agent | None:
    agent = registry.update_status(agent_id, "paused")
    if agent is not None:
        _log_event("pause", agent_id)
    return agent


def resume_agent(agent_id: str, registry: AgentRegistry) -> Agent | None:
    agent = registry.update_status(agent_id, "active")
    if agent is not None:
        _log_event("resume", agent_id)
    return agent


def terminate_agent(agent_id: str, registry: AgentRegistry) -> Agent | None:
    agent = registry.update_status(agent_id, "terminated")
    if agent is not None:
        _log_event("terminate", agent_id)
    return agent
