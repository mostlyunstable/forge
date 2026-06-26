"""EmbeddingService - generates vector embeddings via OpenAI."""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any

import structlog
from openai import AsyncOpenAI

from forge.config.settings import get_settings
from forge.config.metrics import EMBEDDING_CALLS, EMBEDDING_LATENCY

logger = structlog.get_logger()


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingService:
    """Generates and caches text embeddings with bounded memory."""

    MODEL = "nvidia/nv-embedqa-e5-v5"
    DIMENSIONS = 1024
    MAX_CACHE_SIZE = 10000

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: AsyncOpenAI | None = None
        self._cache: OrderedDict[str, list[float]] = OrderedDict()

    def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self._settings.LLM_API_KEY:
                raise EmbeddingError(
                    "LLM_API_KEY is not configured. "
                    "Set the LLM_API_KEY environment variable to use embeddings."
                )
            kwargs = {"api_key": self._settings.LLM_API_KEY}
            if self._settings.LLM_BASE_URL:
                kwargs["base_url"] = self._settings.LLM_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    def _cache_put(self, key: str, value: list[float]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.MAX_CACHE_SIZE:
            self._cache.popitem(last=False)

    async def get_embedding(self, text: str, input_type: str = "passage") -> list[float]:
        """Get embedding for a single text, with caching.

        Args:
            text: The text to embed.
            input_type: "passage" for documents to index, "query" for search queries.
        """
        cache_key = hashlib.md5(f"{input_type}:{text}".encode()).hexdigest()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        start_time = time.perf_counter()
        try:
            client = self._ensure_client()
            response = await client.embeddings.create(
                model=self.MODEL, input=text, extra_body={"input_type": input_type}
            )
            embedding = response.data[0].embedding
            self._cache_put(cache_key, embedding)
            duration = time.perf_counter() - start_time
            EMBEDDING_CALLS.labels(status="success").inc()
            EMBEDDING_LATENCY.observe(duration)
            return embedding
        except Exception as e:
            duration = time.perf_counter() - start_time
            EMBEDDING_CALLS.labels(status="error").inc()
            EMBEDDING_LATENCY.observe(duration)
            logger.error("embedding_call_failed", error=str(e), duration=duration)
            raise

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts. Raises on partial failure."""
        uncached: list[tuple[int, str]] = []
        results: list[list[float] | None] = [None] * len(texts)

        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                results[i] = self._cache[cache_key]
            else:
                uncached.append((i, text))

        if uncached:
            start_time = time.perf_counter()
            try:
                client = self._ensure_client()
                response = await client.embeddings.create(
                    model=self.MODEL,
                    input=[t for _, t in uncached],
                    extra_body={"input_type": "passage"},
                )
                for (idx, text), data in zip(uncached, response.data):
                    cache_key = hashlib.md5(text.encode()).hexdigest()
                    self._cache_put(cache_key, data.embedding)
                    results[idx] = data.embedding
                duration = time.perf_counter() - start_time
                EMBEDDING_CALLS.labels(status="success").inc()
                EMBEDDING_LATENCY.observe(duration)
            except Exception as e:
                duration = time.perf_counter() - start_time
                EMBEDDING_CALLS.labels(status="error").inc()
                EMBEDDING_LATENCY.observe(duration)
                logger.error("embedding_batch_call_failed", error=str(e), duration=duration)
                raise

        if any(r is None for r in results):
            missing = [i for i, r in enumerate(results) if r is None]
            raise EmbeddingError(f"Failed to generate embeddings for texts at indices: {missing}")

        return results  # type: ignore[return-value]

    def clear_cache(self) -> None:
        self._cache.clear()
