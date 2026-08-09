from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

PRIORITY_WEIGHTS = {"p0": 9, "p1": 6, "p2": 3}
IMPACT_WEIGHTS = {"high": 9, "medium": 6, "low": 3}
RISK_WEIGHTS = {"low": 3, "medium": 2, "high": 1}
ACTIVE_STATUSES = {"todo", "blocked", "in_progress", "validating"}



def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}



def _is_active(item: dict[str, Any]) -> bool:
    return item["status"] in ACTIVE_STATUSES



def active_blockers(item: dict[str, Any], items_by_id: dict[str, dict[str, Any]]) -> list[str]:
    return [blocker for blocker in item["blocked_by"] if _is_active(items_by_id[blocker])]


def _build_path_resolver(items_by_id: dict[str, dict[str, Any]]) -> Callable[[str], tuple[str, ...]]:
    """Create a cached resolver for dependency chains within one item graph."""

    @lru_cache(maxsize=None)
    def _path(current_id: str) -> tuple[str, ...]:
        blockers = active_blockers(items_by_id[current_id], items_by_id)
        if not blockers:
            return (current_id,)
        best = max(
            (_path(blocker) for blocker in blockers),
            key=lambda path: (len(path), sum(IMPACT_WEIGHTS[items_by_id[node]["impact"]] for node in path)),
        )
        return (current_id, *best)

    return _path


def build_dependency_path(
    item_id: str,
    items_by_id: dict[str, dict[str, Any]],
    resolver: Callable[[str], tuple[str, ...]] | None = None,
) -> list[str]:
    resolver = resolver or _build_path_resolver(items_by_id)
    return list(resolver(item_id))


def dependency_depth(
    item: dict[str, Any],
    items_by_id: dict[str, dict[str, Any]],
    resolver: Callable[[str], tuple[str, ...]] | None = None,
) -> int:
    return max(len(build_dependency_path(item["id"], items_by_id, resolver=resolver)) - 1, 0)

def critical_path_candidates(items: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    return critical_path_candidates_with_context(items, _index(items), limit=limit)


def critical_path_candidates_with_context(
    items: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
    limit: int = 10,
    resolver: Callable[[str], tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    resolver = resolver or _build_path_resolver(items_by_id)
    ranked: list[dict[str, Any]] = []
    for item in items:
        if not _is_active(item):
            continue
        path = build_dependency_path(item["id"], items_by_id, resolver=resolver)
        score = (
            PRIORITY_WEIGHTS[item["priority"]] * 2
            + IMPACT_WEIGHTS[item["impact"]] * 2
            + len(path) * 3
            - RISK_WEIGHTS[item["risk"]]
        )
        ranked.append(
            {
                "id": item["id"],
                "title": item["title"],
                "section": item["section"],
                "status": item["status"],
                "score": score,
                "dependency_depth": len(path) - 1,
                "blocked_chain": path,
            }
        )
    return sorted(ranked, key=lambda entry: (-entry["score"], -entry["dependency_depth"], entry["id"]))[:limit]



def quick_wins(items: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    return quick_wins_with_context(items, _index(items), limit=limit)


def quick_wins_with_context(
    items: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
    limit: int = 10,
    resolver: Callable[[str], tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    resolver = resolver or _build_path_resolver(items_by_id)
    candidates: list[dict[str, Any]] = []
    for item in items:
        if not _is_active(item) or item["impact"] != "high" or item["risk"] != "low":
            continue
        if active_blockers(item, items_by_id):
            continue
        depth = dependency_depth(item, items_by_id, resolver=resolver)
        if depth > 1:
            continue
        score = PRIORITY_WEIGHTS[item["priority"]] + IMPACT_WEIGHTS[item["impact"]] + RISK_WEIGHTS[item["risk"]] - depth
        candidates.append(
            {
                "id": item["id"],
                "title": item["title"],
                "section": item["section"],
                "status": item["status"],
                "dependency_depth": depth,
                "score": score,
            }
        )
    return sorted(candidates, key=lambda entry: (-entry["score"], entry["dependency_depth"], entry["id"]))[:limit]



def blocked_items_report(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return blocked_items_report_with_context(items, _index(items))


def blocked_items_report_with_context(
    items: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
    resolver: Callable[[str], tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    resolver = resolver or _build_path_resolver(items_by_id)
    blocked: list[dict[str, Any]] = []
    for item in items:
        blockers = active_blockers(item, items_by_id)
        if blockers:
            blocked.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "section": item["section"],
                    "status": item["status"],
                    "active_blockers": blockers,
                    "dependency_depth": dependency_depth(item, items_by_id, resolver=resolver),
                }
            )
    return sorted(blocked, key=lambda entry: (-entry["dependency_depth"], entry["id"]))
