from __future__ import annotations

import asyncio

import pytest

from fractalmesh.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_run_once_default_cycle() -> None:
    state = await Orchestrator().run_once()
    assert state["cycle"] == 1
    assert state["plan"] == ["noop"]


@pytest.mark.asyncio
async def test_run_once_accepts_existing_state() -> None:
    state = await Orchestrator().run_once(
        {
            "cycle": 3,
            "observations": [],
            "reasoning": [],
            "plan": [],
            "actions": [],
            "rewards": [],
        }
    )
    assert state["cycle"] == 4


@pytest.mark.asyncio
async def test_custom_sync_hooks() -> None:
    orchestrator = Orchestrator(
        observer=lambda state: ["obs"],
        reasoner=lambda state: ["reasoned"],
        planner=lambda state: ["act-now"],
    )
    state = await orchestrator.run_once()
    assert state["observations"] == ["obs"]
    assert state["reasoning"] == ["reasoned"]
    assert state["plan"] == ["act-now"]


@pytest.mark.asyncio
async def test_custom_async_hooks() -> None:
    async def actor(state):
        return [{"action": "async", "status": "done"}]

    async def learner(state):
        return [0.9]

    orchestrator = Orchestrator(actor=actor, learner=learner)
    state = await orchestrator.run_once()
    assert state["actions"][0]["action"] == "async"
    assert state["rewards"] == [0.9]


@pytest.mark.asyncio
async def test_run_daemon_can_be_cancelled() -> None:
    orchestrator = Orchestrator()
    task = asyncio.create_task(orchestrator.run_daemon(tick_interval=1))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
