from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

AgentStatus = Literal["active", "paused", "terminated"]


@dataclass
class Agent:
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "general"
    capabilities: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: AgentStatus = "active"
    config: dict[str, Any] = field(default_factory=dict)
