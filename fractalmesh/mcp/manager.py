from __future__ import annotations

from typing import Any

from .client import MCPClient


class MCPManager:
    def __init__(self) -> None:
        self.servers: list[MCPClient] = []
        self._next_index = 0

    def add_server(self, config: dict[str, Any]) -> MCPClient:
        server = MCPClient(**config)
        self.servers.append(server)
        return server

    def remove_server(self, name: str) -> None:
        self.servers = [server for server in self.servers if server.name != name]
        self._next_index %= max(len(self.servers), 1)

    def get_healthy_servers(self) -> list[MCPClient]:
        return [server for server in self.servers if server.health_check()]

    def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        healthy = self.get_healthy_servers()
        if not healthy:
            raise RuntimeError("No healthy MCP servers available")
        attempts = 0
        while attempts < len(healthy):
            server = healthy[(self._next_index + attempts) % len(healthy)]
            try:
                result = server.call(tool_name, args)
                self._next_index = (self._next_index + attempts + 1) % len(healthy)
                return result
            except Exception:
                attempts += 1
        raise RuntimeError(f"All MCP servers failed for tool {tool_name}")

    def discover_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for server in self.get_healthy_servers():
            for tool in server.available_tools:
                key = (server.name, tool.get("name", ""))
                if key in seen:
                    continue
                seen.add(key)
                payload = dict(tool)
                payload.setdefault("server_name", server.name)
                tools.append(payload)
        return tools
