from __future__ import annotations

import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import Any

LOGGER = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = text.split() or [text]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index, byte in enumerate(digest):
                slot = (byte + index) % self.dimensions
                sign = -1.0 if byte % 2 else 1.0
                vector[slot] += sign * ((byte / 255.0) or 0.01)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def get_embedding_provider(config: Any) -> EmbeddingProvider:
    provider_name = getattr(config, "embedding_provider", None)
    if provider_name is None and isinstance(config, dict):
        provider_name = config.get("embedding_provider")
    provider_name = provider_name or "hash"
    if provider_name == "hash":
        return HashEmbeddingProvider()
    LOGGER.warning("Unsupported embedding provider %s, falling back to hash", provider_name)
    return HashEmbeddingProvider()
