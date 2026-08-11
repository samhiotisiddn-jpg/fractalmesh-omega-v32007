from __future__ import annotations

from typing import Any

from fractalmesh.memory.vector_store import VectorStore

from .embeddings import EmbeddingProvider, HashEmbeddingProvider
from .graph import KnowledgeGraph


class GraphRAGRetriever:
    def __init__(
        self,
        vector_store: VectorStore,
        knowledge_graph: KnowledgeGraph,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_embedding = self.embedding_provider.embed(query)
        vector_hits = self.vector_store.search(query_embedding, limit=max(top_k * 2, 1))
        graph_entities = self.knowledge_graph.extract_entities(query)
        related_entities: set[str] = {item["entity_id"] for item in graph_entities}
        for entity in graph_entities:
            traversed = self.knowledge_graph.multi_hop_traverse(entity["entity_id"])
            related_entities.update(edge["to_id"] for edge in traversed)
        results: list[dict[str, Any]] = []
        for hit in vector_hits:
            metadata = hit.get("metadata", {})
            linked = set(metadata.get("entities", []))
            graph_bonus = 0.15 * len(linked & related_entities)
            score = float(hit.get("score", 0.0)) + graph_bonus
            results.append(
                {
                    "content": hit.get("content", ""),
                    "score": score,
                    "provenance": metadata.get("source", "vector_store"),
                    "confidence": max(0.0, min(1.0, score)),
                }
            )
        if not results and related_entities:
            for entity_id in related_entities:
                entity = self.knowledge_graph.entities.get(entity_id)
                if entity is None:
                    continue
                results.append(
                    {
                        "content": str(entity["properties"]),
                        "score": 0.1,
                        "provenance": "knowledge_graph",
                        "confidence": 0.1,
                    }
                )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
