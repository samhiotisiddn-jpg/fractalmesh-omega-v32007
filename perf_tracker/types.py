from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

Status = Literal["todo", "blocked", "in_progress", "validating", "done"]
Priority = Literal["p0", "p1", "p2"]
Level = Literal["high", "medium", "low"]


class TrackerItem(TypedDict):
    id: str
    title: str
    upstream_ref: str
    section: str
    status: Status
    priority: Priority
    impact: Level
    risk: Level
    blocked_by: list[str]
    owner: NotRequired[str | None]
    notes: NotRequired[str | None]
    updated_at: NotRequired[str | None]


class TrackerSection(TypedDict):
    name: str
    items: list[TrackerItem]


class TrackerDocument(TypedDict):
    source_issue: str
    source_title: str
    sections: list[TrackerSection]
