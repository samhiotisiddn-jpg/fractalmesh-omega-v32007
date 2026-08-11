from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree


def load_sources_from_env() -> list[str]:
    raw = os.getenv("RSS_SOURCES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_sources_from_file(path: str) -> list[str]:
    source_path = Path(path)
    if source_path.suffix.lower() == ".json":
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("sources", [])
        return [str(item) for item in payload]
    tree = ElementTree.parse(source_path)
    return [
        outline.attrib["xmlUrl"]
        for outline in tree.findall(".//outline")
        if outline.attrib.get("xmlUrl")
    ]


def export_opml(sources: list[str], path: str) -> None:
    opml = ElementTree.Element("opml", version="2.0")
    body = ElementTree.SubElement(opml, "body")
    for source in sources:
        ElementTree.SubElement(body, "outline", text=source, xmlUrl=source)
    source_path = Path(path)
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        ElementTree.tostring(opml, encoding="unicode"),
        encoding="utf-8",
    )
