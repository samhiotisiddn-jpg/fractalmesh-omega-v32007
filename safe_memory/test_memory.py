"""Tests for SuperLocalMemory."""

import pytest

from .memory import MemoryTier, SuperLocalMemory


def test_add_and_get():
    mem = SuperLocalMemory(":memory:")
    m = mem.add("hello world", MemoryTier.SHORT_TERM, confidence=0.8)
    assert m.content == "hello world"
    assert mem.get(m.id) == m


def test_tiered_search():
    mem = SuperLocalMemory(":memory:")
    mem.add("keep me", MemoryTier.LONG_TERM_EXPLICIT, confidence=0.9)
    mem.add("discard me", MemoryTier.SENSORY, confidence=0.1)
    results = mem.search(tier=MemoryTier.LONG_TERM_EXPLICIT)
    assert len(results) == 1
    assert results[0].content == "keep me"


def test_decay_moves_stale_stm():
    mem = SuperLocalMemory(":memory:", stm_ttl_seconds=-1)
    m = mem.add("stale", MemoryTier.SHORT_TERM)
    stats = mem.decay_and_quantize()
    assert stats["moved_to_implicit"] == 1
    reloaded = mem.get(m.id)
    assert reloaded is not None
    assert reloaded.tier == MemoryTier.LONG_TERM_IMPLICIT


def test_soft_prompt_respects_budget():
    mem = SuperLocalMemory(":memory:")
    for i in range(5):
        mem.add(f"fact {i} " * 50, MemoryTier.LONG_TERM_EXPLICIT, confidence=0.9)
    prompt = mem.get_soft_prompt(budget_tokens=80)
    # Should be non-empty but well under the enormous bulk.
    assert prompt
    assert len(prompt.split()) <= 80 + 10  # rough token guard


def test_forget_low_confidence_sensory():
    mem = SuperLocalMemory(":memory:")
    m = mem.add("noise", MemoryTier.SENSORY, confidence=0.04)
    stats = mem.decay_and_quantize()
    assert stats["forgotten"] == 1
    assert mem.get(m.id) is None
