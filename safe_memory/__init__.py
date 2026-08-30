"""Safe, local-first memory tier for the FractalMesh agent swarm.

Implements a minimal SuperLocalMemory-style taxonomy:
- sensory
- short_term
- long_term_explicit
- long_term_implicit

All writes are transactional via SQLite, all data stays local unless the
caller explicitly exports it.
"""

from .memory import Memory, MemoryTier, SuperLocalMemory

__all__ = ["Memory", "MemoryTier", "SuperLocalMemory"]
