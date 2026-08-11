from __future__ import annotations

import re
from collections import deque
from typing import Any


class KnowledgeGraph:
    def __init__(self) -> None:
        self.entities: dict[str, dict[str, Any]] = {}
        self.adjacency: dict[str, list[dict[str, Any]]] = {}

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: dict[str, Any],
    ) -> None:
        self.entities[entity_id] = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "properties": properties,
        }
        self.adjacency.setdefault(entity_id, [])

    def add_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        weight: float = 1.0,
    ) -> None:
        self.adjacency.setdefault(from_id, []).append(
            {
                "from_id": from_id,
                "to_id": to_id,
                "relation_type": relation_type,
                "weight": weight,
            }
        )

    def extract_entities(self, text: str) -> list[dict[str, Any]]:
        matches = sorted(set(re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)))
        return [
            {
                "entity_id": match.lower(),
                "entity_type": "heuristic",
                "properties": {"label": match},
            }
            for match in matches
        ]

    def multi_hop_traverse(self, start_id: str, max_hops: int = 3) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])
        visited = {start_id}
        while queue:
            current, hops = queue.popleft()
            if hops >= max_hops:
                continue
            for edge in self.adjacency.get(current, []):
                payload = dict(edge)
                payload["hops"] = hops + 1
                results.append(payload)
                neighbor = edge["to_id"]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, hops + 1))
        return results
