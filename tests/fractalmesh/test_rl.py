from __future__ import annotations

import sqlite3

from fractalmesh.rl.engine import RLEngine
from fractalmesh.rl.rewards import RewardModel
from fractalmesh.rl.store import RLStore


def test_ucb_selects_unseen_action_first() -> None:
    engine = RLEngine(actions=["a", "b", "c"], exploration_rate=0.0)
    action = engine.select_action({})
    assert action in {"a", "b", "c"}
    assert engine.action_counts[action] == 0


def test_update_adjusts_action_values() -> None:
    engine = RLEngine(actions=["a"], exploration_rate=0.0)
    engine.update("a", 1.0)
    engine.update("a", 0.0)
    assert engine.action_counts["a"] == 2
    assert engine.action_values["a"] == 0.5


def test_select_action_prefers_better_ucb_after_updates() -> None:
    engine = RLEngine(actions=["a", "b"], exploration_rate=0.0)
    engine.update("a", 1.0)
    engine.update("b", 0.1)
    engine.action_counts["a"] = 10
    engine.action_counts["b"] = 1
    assert engine.select_action({}) == "b"


def test_reward_model_tracks_ema_and_regret() -> None:
    model = RewardModel(alpha=0.5)
    model.update("latency", 1.0)
    model.update("latency", 0.0)
    assert model.get_ema("latency") == 0.5
    assert model.get_regret() == 1.0
    assert model.shape_reward(1.0, "latency") == 1.05


def test_rl_store_save_load_and_checkpoint(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'rl.db'}"
    store = RLStore(db_url)
    store.save_step("explore", 0.7, {"state": "x"})
    store.save_policy({"explore": {"value_estimate": 0.7, "count": 1}})
    store.checkpoint("baseline")
    policy = store.load_policy()
    assert policy["explore"]["count"] == 1
    conn = sqlite3.connect(tmp_path / 'rl.db')
    total = conn.execute("SELECT COUNT(*) FROM rl_actions").fetchone()[0]
    checkpoints = conn.execute("SELECT COUNT(*) FROM rl_checkpoints").fetchone()[0]
    assert total == 1
    assert checkpoints == 1
