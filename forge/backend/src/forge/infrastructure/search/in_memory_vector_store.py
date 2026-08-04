"""InMemoryVectorStore - lightweight vector store for dev mode."""

from __future__ import annotations

import math
import time
from typing import Any
from uuid import UUID

import structlog

from forge.config.metrics import VECTOR_SEARCH_CALLS, VECTOR_SEARCH_LATENCY

logger = structlog.get_logger()

COLLECTIONS = {"code", "decisions", "bugs"}


class InMemoryVectorStore:
    """Simple in-memory vector store for development/testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict[Any, dict[str, Any]]] = {col: {} for col in COLLECTIONS}

    async def init_collections(self) -> None:
        logger.info("in_memory_vector_store.init_collections")

    async def upsert_code(
        self,
        project_id: UUID,
        file_path: str,
        entry_type: str,
        name: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        point_id = hash(f"{project_id}:{file_path}:{name}") % (2**63)
        self._store["code"][point_id] = {
            "id": point_id,
            "vector": embedding,
            "payload": {
                "project_id": str(project_id),
                "file_path": file_path,
                "entry_type": entry_type,
                "name": name,
                "content": content,
                "metadata": metadata,
            },
        }

    async def upsert_decision(
        self,
        project_id: UUID,
        decision_id: UUID,
        title: str,
        decision: str,
        reason: str,
        embedding: list[float],
    ) -> None:
        self._store["decisions"][str(decision_id)] = {
            "id": str(decision_id),
            "vector": embedding,
            "payload": {
                "project_id": str(project_id),
                "title": title,
                "decision": decision,
                "reason": reason,
            },
        }

    async def upsert_bug(
        self,
        project_id: UUID,
        bug_id: UUID,
        title: str,
        problem: str,
        solution: str | None,
        embedding: list[float],
    ) -> None:
        self._store["bugs"][str(bug_id)] = {
            "id": str(bug_id),
            "vector": embedding,
            "payload": {
                "project_id": str(project_id),
                "title": title,
                "problem": problem,
                "solution": solution,
            },
        }

    async def search_code(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._search("code", query_embedding, project_id, limit)

    async def search_decisions(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._search("decisions", query_embedding, project_id, limit)

    async def search_bugs(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._search("bugs", query_embedding, project_id, limit)

    async def delete_by_project(self, project_id: UUID) -> None:
        pid = str(project_id)
        for col in COLLECTIONS:
            self._store[col] = {
                k: v for k, v in self._store[col].items() if v["payload"].get("project_id") != pid
            }

    async def _search(
        self,
        collection: str,
        query: list[float],
        project_id: UUID | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        start_time = time.perf_counter()
        try:
            points = list(self._store[collection].values())
            if project_id is not None:
                pid = str(project_id)
                points = [p for p in points if p["payload"].get("project_id") == pid]

            scored = []
            for p in points:
                score = self._cosine_similarity(query, p["vector"])
                scored.append({"id": p["id"], "score": score, "payload": p["payload"]})
            scored.sort(key=lambda x: x["score"], reverse=True)

            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection=collection, status="success").inc()
            VECTOR_SEARCH_LATENCY.labels(collection=collection).observe(duration)
            return scored[:limit]
        except Exception as e:
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection=collection, status="error").inc()
            VECTOR_SEARCH_LATENCY.labels(collection=collection).observe(duration)
            logger.error("vector_search_failed", collection=collection, error=str(e))
            raise

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


in_memory_vector_store = InMemoryVectorStore()
