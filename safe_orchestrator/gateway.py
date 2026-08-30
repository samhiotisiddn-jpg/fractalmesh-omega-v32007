"""Policy gateway: capability checks, risk scoring, approval gating, kill-switch."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .registry import RiskClass, ToolManifest, ToolRegistry


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: Decision
    reason: str
    risk_score: float


class PolicyGateway:
    """Stateful risk evaluator for tool invocations.

    Tracks per-agent history and triggers a cooldown (kill-switch) after
    repeated denials within the configured window.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        denied_window_seconds: int = 600,
        denied_threshold: int = 3,
        cooldown_seconds: int = 600,
    ):
        self.registry = registry
        self.denied_window = denied_window_seconds
        self.denied_threshold = denied_threshold
        self.cooldown_seconds = cooldown_seconds

        self._agent_capabilities: dict[str, set[str]] = {}
        self._denial_history: dict[str, list[float]] = {}
        self._cooldown_until: dict[str, float] = {}
        self._approval_callbacks: dict[
            str, Callable[[ToolManifest, dict[str, Any]], bool]
        ] = {}
        self._audit_callback: Callable[[dict[str, Any]], None] | None = None

    def assign_capabilities(self, agent_id: str, capabilities: set[str]) -> None:
        self._agent_capabilities[agent_id] = set(capabilities)

    def set_approval_callback(
        self,
        agent_id: str,
        callback: Callable[[ToolManifest, dict[str, Any]], bool],
    ) -> None:
        self._approval_callbacks[agent_id] = callback

    def set_audit_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._audit_callback = callback

    def evaluate(
        self,
        agent_id: str,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        approval_token: str | None = None,
    ) -> PolicyDecision:
        parameters = parameters or {}

        # 1. Cooldown / kill-switch
        now = time.time()
        cooldown_until = self._cooldown_until.get(agent_id, 0.0)
        if now < cooldown_until:
            return PolicyDecision(
                Decision.DENY,
                f"Agent {agent_id} is in kill-switch cooldown until {cooldown_until}",
                risk_score=1.0,
            )

        # 2. Tool exists and is trusted
        pair = self.registry.get(tool_name)
        if pair is None:
            self._record_denial(agent_id, now)
            return PolicyDecision(
                Decision.DENY,
                f"Tool {tool_name} not found or not trusted",
                risk_score=0.9,
            )
        manifest, _ = pair

        # 3. Capability check
        agent_caps = self._agent_capabilities.get(agent_id, set())
        missing = set(manifest.capabilities) - agent_caps
        if missing:
            self._record_denial(agent_id, now)
            return PolicyDecision(
                Decision.DENY,
                f"Agent lacks capabilities: {sorted(missing)}",
                risk_score=0.7,
            )

        # 4. Risk scoring (heuristic)
        risk_score = self._score(manifest, parameters)

        # 5. Approval gating
        if manifest.requires_approval and not approval_token:
            return PolicyDecision(
                Decision.APPROVAL_REQUIRED,
                f"Tool {tool_name} requires operator approval",
                risk_score=risk_score,
            )

        # If an approval token is provided, in a real system it would be
        # validated against a short-lived signed token from the operator.

        self._audit(
            {
                "event": "tool_evaluated",
                "agent_id": agent_id,
                "tool": tool_name,
                "decision": Decision.ALLOW.value,
                "risk_score": risk_score,
                "timestamp": now,
            }
        )
        return PolicyDecision(Decision.ALLOW, "Allowed", risk_score=risk_score)

    def _score(self, manifest: ToolManifest, parameters: dict[str, Any]) -> float:
        base = {
            RiskClass.LOW: 0.1,
            RiskClass.MEDIUM: 0.35,
            RiskClass.HIGH: 0.65,
            RiskClass.CRITICAL: 0.9,
        }[manifest.risk_class]

        # Increase score for payloads with suspicious patterns.
        payload_str = json.dumps(parameters, sort_keys=True, default=str)
        if any(p in payload_str for p in ("../../", "../", "https://", "http://")):
            base += 0.1
        return min(base, 1.0)

    def _record_denial(self, agent_id: str, now: float) -> None:
        history = self._denial_history.setdefault(agent_id, [])
        cutoff = now - self.denied_window
        history[:] = [t for t in history if t > cutoff]
        history.append(now)
        if len(history) >= self.denied_threshold:
            self._cooldown_until[agent_id] = now + self.cooldown_seconds
            self._audit(
                {
                    "event": "kill_switch_triggered",
                    "agent_id": agent_id,
                    "denial_count": len(history),
                    "cooldown_until": self._cooldown_until[agent_id],
                    "timestamp": now,
                }
            )

    def is_in_cooldown(self, agent_id: str) -> bool:
        return time.time() < self._cooldown_until.get(agent_id, 0.0)

    def reset_cooldown(self, agent_id: str) -> None:
        self._cooldown_until.pop(agent_id, None)
        self._denial_history.pop(agent_id, None)

    def _audit(self, record: dict[str, Any]) -> None:
        if self._audit_callback:
            self._audit_callback(record)
