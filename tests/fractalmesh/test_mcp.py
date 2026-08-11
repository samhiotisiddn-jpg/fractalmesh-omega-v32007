from __future__ import annotations

import pytest

from fractalmesh.mcp.client import MCPClient
from fractalmesh.mcp.manager import MCPManager
from fractalmesh.mcp.registry import MCPToolRegistry


def test_client_connect_and_disconnect() -> None:
    client = MCPClient(name="a", transport="sse", endpoint="http://example.com")
    client.connect()
    assert client.connected is True
    client.disconnect()
    assert client.connected is False


def test_circuit_breaker_opens_after_failures() -> None:
    client = MCPClient(name="a", transport="sse", endpoint="http://example.com")
    client._execute_call = lambda tool, args: (_ for _ in ()).throw(RuntimeError("boom"))
    for _ in range(3):
        with pytest.raises(RuntimeError):
            client.call("tool", {})
    assert client.health_check() is False
    with pytest.raises(RuntimeError):
        client.call("tool", {})


def test_successful_call_resets_failures() -> None:
    client = MCPClient(name="a", transport="sse", endpoint="http://example.com")
    client.failure_count = 2
    result = client.call("tool", {"x": 1})
    assert result["tool"] == "tool"
    assert client.failure_count == 0


def test_tool_registry_register_lookup_and_list(tmp_path) -> None:
    registry = MCPToolRegistry(f"sqlite:///{tmp_path / 'mcp.db'}")
    registry.register_tool(
        {
            "tool_id": "1",
            "name": "search",
            "description": "Search docs",
            "server_name": "alpha",
            "schema": {"type": "object"},
        }
    )
    looked_up = registry.lookup("search")
    listed = registry.list_tools()
    assert looked_up is not None
    assert looked_up["server_name"] == "alpha"
    assert len(listed) == 1


def test_manager_round_robin_failover_and_discovery() -> None:
    manager = MCPManager()
    failing = MCPClient(name="bad", transport="sse", endpoint="http://bad")
    failing._execute_call = lambda tool, args: (_ for _ in ()).throw(RuntimeError("boom"))
    healthy = MCPClient(name="good", transport="sse", endpoint="http://good")
    healthy.available_tools.append({"name": "search", "description": "ok"})
    manager.servers = [failing, healthy]
    result = manager.call_tool("search", {"q": "x"})
    discovered = manager.discover_tools()
    assert result["server"] == "good"
    assert discovered[0]["server_name"] == "good"
