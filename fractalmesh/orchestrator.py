from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict


class OrchestratorState(TypedDict):
    cycle: int
    observations: list[Any]
    reasoning: list[str]
    plan: list[str]
    actions: list[dict[str, Any]]
    rewards: list[float]


Hook = Callable[[OrchestratorState], Any | Awaitable[Any]]


class Orchestrator:
    def __init__(
        self,
        observer: Hook | None = None,
        reasoner: Hook | None = None,
        planner: Hook | None = None,
        actor: Hook | None = None,
        learner: Hook | None = None,
    ) -> None:
        self._observer = observer
        self._reasoner = reasoner
        self._planner = planner
        self._actor = actor
        self._learner = learner

    async def _resolve(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    async def observe(self, state: OrchestratorState) -> list[Any]:
        if self._observer is not None:
            return await self._resolve(self._observer(state))
        return [{"cycle": state["cycle"]}]

    async def reason(self, state: OrchestratorState) -> list[str]:
        if self._reasoner is not None:
            return await self._resolve(self._reasoner(state))
        return [f"Observed {len(state['observations'])} items"]

    async def plan(self, state: OrchestratorState) -> list[str]:
        if self._planner is not None:
            return await self._resolve(self._planner(state))
        return ["noop"] if state["observations"] else []

    async def act(self, state: OrchestratorState) -> list[dict[str, Any]]:
        if self._actor is not None:
            return await self._resolve(self._actor(state))
        return [{"action": step, "status": "completed"} for step in state["plan"]]

    async def learn(self, state: OrchestratorState) -> list[float]:
        if self._learner is not None:
            return await self._resolve(self._learner(state))
        return [1.0 for _ in state["actions"]]

    async def run_once(self, state: OrchestratorState | None = None) -> OrchestratorState:
        current: OrchestratorState = state or {
            "cycle": 0,
            "observations": [],
            "reasoning": [],
            "plan": [],
            "actions": [],
            "rewards": [],
        }
        current = dict(current)
        current["cycle"] = current.get("cycle", 0) + 1
        current["observations"] = await self.observe(current)
        current["reasoning"] = await self.reason(current)
        current["plan"] = await self.plan(current)
        current["actions"] = await self.act(current)
        current["rewards"] = await self.learn(current)
        return current

    async def run_daemon(self, tick_interval: int = 60) -> None:
        state: OrchestratorState | None = None
        while True:
            state = await self.run_once(state)
            await asyncio.sleep(tick_interval)
