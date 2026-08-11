from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MAX_JSON_BYTES = 50 * 1024 * 1024
DEFAULT_DB_PATH = Path("tracker/perf_tracker.db")


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _env_int(name: str, default: int, minimum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def get_max_json_bytes() -> int:
    return _env_int("PERF_TRACKER_MAX_JSON_BYTES", DEFAULT_MAX_JSON_BYTES, minimum=1024)


def get_db_path() -> Path:
    raw = os.getenv("PERF_TRACKER_DB_PATH")
    return Path(raw) if raw else DEFAULT_DB_PATH
