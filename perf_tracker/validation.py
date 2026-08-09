from __future__ import annotations

from datetime import datetime
from typing import Any

from perf_tracker.io import list_items
from perf_tracker.types import TrackerDocument

ALLOWED_STATUSES = {"todo", "blocked", "in_progress", "validating", "done"}
ALLOWED_PRIORITIES = {"p0", "p1", "p2"}
ALLOWED_LEVELS = {"high", "medium", "low"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "upstream_ref",
    "section",
    "status",
    "priority",
    "impact",
    "risk",
    "blocked_by",
}


class ValidationError(ValueError):
    """Raised when tracker data is invalid."""



def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)



def _validate_iso8601(value: str, field_name: str, item_id: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{item_id}: {field_name} must be ISO-8601, got {value!r}") from exc



def validate_document(document: TrackerDocument) -> list[dict[str, Any]]:
    _require(isinstance(document, dict), "tracker document must be an object")
    _require(isinstance(document.get("source_issue"), str) and document["source_issue"], "source_issue is required")
    _require(isinstance(document.get("source_title"), str) and document["source_title"], "source_title is required")
    sections = document.get("sections")
    _require(isinstance(sections, list) and sections, "sections must be a non-empty array")

    seen_sections: set[str] = set()
    ids: set[str] = set()
    normalized_items: list[dict[str, Any]] = []

    for section in sections:
        _require(isinstance(section, dict), "each section must be an object")
        section_name = section.get("name")
        _require(isinstance(section_name, str) and section_name, "section name is required")
        _require(section_name not in seen_sections, f"duplicate section {section_name!r}")
        seen_sections.add(section_name)
        items = section.get("items")
        _require(isinstance(items, list) and items, f"section {section_name!r} must contain items")
        for item in items:
            _require(isinstance(item, dict), f"section {section_name!r} contains a non-object item")
            missing = sorted(REQUIRED_FIELDS - set(item))
            _require(not missing, f"item missing required fields: {', '.join(missing)}")
            item_id = item["id"]
            _require(isinstance(item_id, str) and item_id, "item id must be a non-empty string")
            _require(item_id not in ids, f"duplicate item id {item_id!r}")
            ids.add(item_id)
            _require(item["section"] == section_name, f"{item_id}: section field must match parent section")
            _require(item["status"] in ALLOWED_STATUSES, f"{item_id}: invalid status {item['status']!r}")
            _require(item["priority"] in ALLOWED_PRIORITIES, f"{item_id}: invalid priority {item['priority']!r}")
            _require(item["impact"] in ALLOWED_LEVELS, f"{item_id}: invalid impact {item['impact']!r}")
            _require(item["risk"] in ALLOWED_LEVELS, f"{item_id}: invalid risk {item['risk']!r}")
            _require(isinstance(item["blocked_by"], list), f"{item_id}: blocked_by must be an array")
            _require(all(isinstance(blocker, str) and blocker for blocker in item["blocked_by"]), f"{item_id}: blocked_by entries must be non-empty strings")
            for optional_field in ("owner", "notes", "updated_at"):
                if optional_field in item and item[optional_field] is not None:
                    _require(isinstance(item[optional_field], str) and item[optional_field], f"{item_id}: {optional_field} must be a non-empty string when present")
            if item.get("updated_at"):
                _validate_iso8601(item["updated_at"], "updated_at", item_id)
            normalized_items.append(item)

    known_ids = {item["id"] for item in normalized_items}
    for item in normalized_items:
        unknown = [blocker for blocker in item["blocked_by"] if blocker not in known_ids]
        _require(not unknown, f"{item['id']}: unknown blockers {unknown}")

    items_by_id = {item["id"]: item for item in normalized_items}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def _visit(item_id: str) -> None:
        if item_id in visited:
            return
        if item_id in visiting:
            cycle_start = stack.index(item_id)
            cycle = " -> ".join(stack[cycle_start:] + [item_id])
            raise ValidationError(f"dependency cycle detected involving {cycle}")
        visiting.add(item_id)
        stack.append(item_id)
        for blocker in items_by_id[item_id]["blocked_by"]:
            _visit(blocker)
        stack.pop()
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in sorted(items_by_id):
        _visit(item_id)

    return normalized_items



def summarize_statuses(document: TrackerDocument) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    for item in list_items(document):
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts
