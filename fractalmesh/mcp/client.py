from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class MCPClient:
    name: str
    transport: Literal["stdio", "sse"]
    endpoint: str
    timeout: int = 30
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    failure_count: int = 0
    circuit_open_until: float = 0.0
    connected: bool = False

    def connect(self) -> None:
        if self._circuit_is_open():
            raise RuntimeError("Circuit breaker is open")
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def _circuit_is_open(self) -> bool:
        return time.time() < self.circuit_open_until

    def health_check(self) -> bool:
        return not self._circuit_is_open()

    def _execute_call(self, tool: str, args: dict[str, Any]) -> Any:
        return {"server": self.name, "tool": tool, "args": args}

    def call(self, tool: str, args: dict[str, Any]) -> Any:
        if self._circuit_is_open():
            raise RuntimeError("Circuit breaker is open")
        if not self.connected:
            self.connect()
        try:
            result = self._execute_call(tool, args)
        except Exception:
            self.failure_count += 1
            if self.failure_count >= 3:
                self.circuit_open_until = time.time() + 60
            raise
        self.failure_count = 0
        self.circuit_open_until = 0.0
        return result
