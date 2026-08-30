"""Policy-gated Model Context Protocol (MCP) orchestration layer.

Provides:
- Tool manifest validation and registration.
- Capability-based access control.
- History-aware risk scoring and kill-switch logic.
- Middleware hooks for auditing and human approval.
"""

from .gateway import Decision, PolicyDecision, PolicyGateway
from .registry import RiskClass, ToolManifest, ToolRegistry

__all__ = [
    "Decision",
    "PolicyDecision",
    "PolicyGateway",
    "RiskClass",
    "ToolManifest",
    "ToolRegistry",
]
