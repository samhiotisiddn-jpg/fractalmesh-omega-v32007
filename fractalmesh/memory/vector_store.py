from __future__ import annotations

import json
import math
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


def _sqlite_path(database_url: str) -> str:
    return database_url.replace("sqlite:///", "", 1)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


class VectorStore(ABC):
    @abstractmethod
    def store(
        self,
        record_id: str,
        embedding: list[float],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, record_id: str) -> None:
        raise NotImplementedError


class SQLiteVectorStore(VectorStore):
    def __init__(self, database_url: str = "sqlite:///fractalmesh.db") -> None:
        db_path = Path(_sqlite_path(database_url))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vectors (
                record_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def store(
        self,
        record_id: str,
        embedding: list[float],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO vectors(record_id, content, embedding_json, metadata_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                content=excluded.content,
                embedding_json=excluded.embedding_json,
                metadata_json=excluded.metadata_json
            """,
            (record_id, content, json.dumps(embedding), json.dumps(metadata or {})),
        )
        self.conn.commit()

    def search(self, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM vectors").fetchall()
        scored = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            scored.append(
                {
                    "record_id": row["record_id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata_json"]),
                    "score": _cosine_similarity(query_embedding, embedding),
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def delete(self, record_id: str) -> None:
        self.conn.execute("DELETE FROM vectors WHERE record_id = ?", (record_id,))
        self.conn.commit()


class ChromaVectorStore(VectorStore):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "fractalmesh",
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is not installed") from exc
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(collection_name)

    def store(
        self,
        record_id: str,
        embedding: list[float],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._collection.upsert(
            ids=[record_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )

    def search(self, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        results = self._collection.query(query_embeddings=[query_embedding], n_results=limit)
        hits: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for record_id, content, metadata, distance in zip(ids, docs, metas, distances):
            hits.append(
                {
                    "record_id": record_id,
                    "content": content,
                    "metadata": metadata,
                    "score": 1.0 / (1.0 + float(distance)),
                }
            )
        return hits

    def delete(self, record_id: str) -> None:
        self._collection.delete(ids=[record_id])
