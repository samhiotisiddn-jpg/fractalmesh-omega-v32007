"""Tests for the orchestrator registry and gateway."""

import pytest

from .gateway import Decision, PolicyGateway
from .registry import RiskClass, ToolManifest, ToolRegistry


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.trust_authority("auth-abc")
    reg.register(
        ToolManifest.from_dict(
            {
                "name": "read_file",
                "version": "1.0.0",
                "authority": "auth-abc",
                "capabilities": ["fs:read"],
                "risk_class": "low",
                "description": "Read a local file.",
            }
        ),
        handler=lambda path: open(path).read(),
    )
    reg.register(
        ToolManifest.from_dict(
            {
                "name": "delete_file",
                "version": "1.0.0",
                "authority": "auth-abc",
                "capabilities": ["fs:write"],
                "risk_class": "critical",
                "description": "Delete a file permanently.",
                "requires_approval": True,
            }
        ),
        handler=lambda path: None,
    )
    return reg


def test_capability_allow(registry):
    gw = PolicyGateway(registry)
    gw.assign_capabilities("agent-1", {"fs:read"})
    decision = gw.evaluate("agent-1", "read_file", {"path": "/tmp/x.txt"})
    assert decision.decision == Decision.ALLOW


def test_capability_deny(registry):
    gw = PolicyGateway(registry)
    gw.assign_capabilities("agent-1", {"fs:read"})
    decision = gw.evaluate("agent-1", "delete_file", {"path": "/tmp/x.txt"})
    assert decision.decision == Decision.DENY


def test_approval_required(registry):
    gw = PolicyGateway(registry)
    gw.assign_capabilities("agent-1", {"fs:write"})
    decision = gw.evaluate("agent-1", "delete_file", {"path": "/tmp/x.txt"})
    assert decision.decision == Decision.APPROVAL_REQUIRED


def test_kill_switch_after_denials(registry):
    gw = PolicyGateway(registry, denied_window_seconds=60, denied_threshold=2)
    gw.assign_capabilities("agent-1", set())
    gw.evaluate("agent-1", "read_file")
    gw.evaluate("agent-1", "delete_file")
    assert gw.is_in_cooldown("agent-1")


def test_tool_shadowing_detected(registry):
    reg = registry
    with pytest.raises(RuntimeError, match="Tool shadowing"):
        reg.register(
            ToolManifest.from_dict(
                {
                    "name": "read_file",
                    "version": "2.0.0",
                    "authority": "auth-abc",
                    "capabilities": ["fs:read"],
                    "risk_class": "low",
                    "description": "Another read_file.",
                }
            ),
            handler=lambda path: None,
        )


def test_untrusted_authority_rejected():
    reg = ToolRegistry()
    with pytest.raises(PermissionError):
        reg.register(
            ToolManifest.from_dict(
                {
                    "name": "bad_tool",
                    "version": "1.0.0",
                    "authority": "untrusted",
                    "capabilities": [],
                    "risk_class": "low",
                    "description": "Should fail.",
                }
            ),
            handler=lambda: None,
        )
