from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from perf_tracker.prioritization import (
    _build_path_resolver,
    blocked_items_report_with_context,
    critical_path_candidates_with_context,
    quick_wins_with_context,
)



def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _default_now(items: list[dict[str, Any]]) -> datetime:
    timestamps = [_parse_dt(item.get("updated_at")) for item in items]
    known = [timestamp for timestamp in timestamps if timestamp is not None]
    return max(known) if known else datetime.now(timezone.utc)


def _score_action(item: dict[str, Any]) -> tuple[int, int, str]:
    status_order = {"in_progress": 0, "validating": 1, "todo": 2, "blocked": 3, "done": 4}
    priority_order = {"p0": 0, "p1": 1, "p2": 2}
    return (status_order[item["status"]], priority_order[item["priority"]], item["id"])



def generate_report(items: list[dict[str, Any]], stale_days: int = 7, now: datetime | None = None) -> dict[str, Any]:
    now = now or _default_now(items)
    items_by_id = {item["id"]: item for item in items}
    resolver = _build_path_resolver(items_by_id)
    section_status_counts: dict[str, dict[str, int]] = defaultdict(Counter)
    global_status_counts: Counter[str] = Counter()

    for item in items:
        section_status_counts[item["section"]][item["status"]] += 1
        global_status_counts[item["status"]] += 1

    critical = critical_path_candidates_with_context(items, items_by_id, limit=5, resolver=resolver)
    wins = quick_wins_with_context(items, items_by_id, limit=5, resolver=resolver)
    blocked = blocked_items_report_with_context(items, items_by_id, resolver=resolver)

    next_actions_by_id: dict[str, dict[str, Any]] = {}
    for entry in wins + critical:
        item = items_by_id[entry["id"]]
        if item["status"] != "done":
            next_actions_by_id[item["id"]] = item
    top_next_actions = sorted(next_actions_by_id.values(), key=_score_action)[:5]

    missing_owners = [item for item in items if item.get("owner") in (None, "") and item["status"] != "done"]
    stale_cutoff = now.timestamp() - stale_days * 86400
    stale_items = []
    for item in items:
        updated_at = _parse_dt(item.get("updated_at"))
        if item["status"] not in {"blocked", "in_progress"} or updated_at is None:
            continue
        if updated_at.timestamp() < stale_cutoff:
            stale_items.append(item)

    active_items = global_status_counts["todo"] + global_status_counts["blocked"] + global_status_counts["in_progress"] + global_status_counts["validating"]
    executive_summary = {
        "total_items": len(items),
        "active_items": active_items,
        "done_items": global_status_counts["done"],
        "blocked_items": len(blocked),
        "critical_path_focus": [entry["id"] for entry in critical[:3]],
        "quick_win_focus": [entry["id"] for entry in wins[:3]],
    }

    return {
        "generated_at": now.isoformat(),
        "executive_summary": executive_summary,
        "global_status_counts": dict(sorted(global_status_counts.items())),
        "section_status_counts": {section: dict(sorted(counts.items())) for section, counts in sorted(section_status_counts.items())},
        "critical_path_candidates": critical,
        "quick_wins": wins,
        "blocked_items": blocked,
        "top_next_actions": [
            {
                "id": item["id"],
                "title": item["title"],
                "section": item["section"],
                "priority": item["priority"],
                "status": item["status"],
            }
            for item in top_next_actions
        ],
        "items_missing_owners": [
            {
                "id": item["id"],
                "title": item["title"],
                "section": item["section"],
                "status": item["status"],
            }
            for item in missing_owners
        ],
        "stale_items": [
            {
                "id": item["id"],
                "title": item["title"],
                "section": item["section"],
                "status": item["status"],
                "updated_at": item.get("updated_at"),
            }
            for item in stale_items
        ],
    }



def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")



def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DeepSeek V4 Perf Tracker Status",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Executive summary",
        f"- Total items: **{report['executive_summary']['total_items']}**",
        f"- Active items: **{report['executive_summary']['active_items']}**",
        f"- Done items: **{report['executive_summary']['done_items']}**",
        f"- Blocked items: **{report['executive_summary']['blocked_items']}**",
        f"- Critical-path focus: {', '.join(report['executive_summary']['critical_path_focus']) or 'none'}",
        f"- Quick-win focus: {', '.join(report['executive_summary']['quick_win_focus']) or 'none'}",
        "",
        "## Section status counts",
    ]
    for section, counts in report["section_status_counts"].items():
        summary = ", ".join(f"{status}: {count}" for status, count in counts.items())
        lines.append(f"- **{section}** — {summary}")

    def _append_table(title: str, rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
        lines.extend(["", f"## {title}"])
        if not rows:
            lines.append("- None")
            return

        def _format_cell(value: Any) -> str:
            if isinstance(value, list):
                return ", ".join(str(entry) for entry in value)
            return str(value)

        lines.append("| " + " | ".join(label for _, label in columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in rows:
            lines.append("| " + " | ".join(_format_cell(row.get(key, "")) for key, _ in columns) + " |")

    _append_table(
        "Top next actions",
        report["top_next_actions"],
        [("id", "ID"), ("priority", "Priority"), ("status", "Status"), ("section", "Section"), ("title", "Title")],
    )
    _append_table(
        "Critical path candidates",
        report["critical_path_candidates"],
        [("id", "ID"), ("status", "Status"), ("dependency_depth", "Depth"), ("score", "Score"), ("title", "Title")],
    )
    _append_table(
        "Quick wins",
        report["quick_wins"],
        [("id", "ID"), ("status", "Status"), ("dependency_depth", "Depth"), ("score", "Score"), ("title", "Title")],
    )
    _append_table(
        "Blocked items",
        report["blocked_items"],
        [("id", "ID"), ("status", "Status"), ("dependency_depth", "Depth"), ("active_blockers", "Active blockers"), ("title", "Title")],
    )
    _append_table(
        "Items missing owners",
        report["items_missing_owners"],
        [("id", "ID"), ("status", "Status"), ("section", "Section"), ("title", "Title")],
    )
    _append_table(
        "Stale items",
        report["stale_items"],
        [("id", "ID"), ("status", "Status"), ("updated_at", "Updated at"), ("title", "Title")],
    )
    lines.append("")
    return "\n".join(lines)



def write_markdown(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(report), encoding="utf-8")
