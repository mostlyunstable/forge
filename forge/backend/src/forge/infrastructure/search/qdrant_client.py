"""QdrantVectorStore - vector search adapter."""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any
from uuid import UUID

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from forge.config.metrics import VECTOR_SEARCH_CALLS, VECTOR_SEARCH_LATENCY
from forge.config.settings import get_settings

logger = structlog.get_logger()

COLLECTIONS = {
    "code": "forge_code",
    "decisions": "forge_decisions",
    "bugs": "forge_bugs",
}

VECTOR_SIZE = 1536


class QdrantVectorStore:
    """Manages vector embeddings in Qdrant for semantic search."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: QdrantClient | None = None

    def _ensure_client(self) -> QdrantClient:
        if self._client is None:
            if self._settings.QDRANT_HOST == "memory":
                self._client = QdrantClient(location=":memory:")
            else:
                self._client = QdrantClient(
                    host=self._settings.QDRANT_HOST,
                    port=self._settings.QDRANT_PORT,
                )
        return self._client

    async def init_collections(self) -> None:
        """Create collections if they don't exist."""
        client = self._ensure_client()
        for name in COLLECTIONS.values():
            try:
                await asyncio.to_thread(client.get_collection, name)
            except Exception:
                await asyncio.to_thread(
                    client.create_collection,
                    collection_name=name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )

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
        semantic_hash = metadata.get("semantic_hash", "")
        if not semantic_hash:
            import re

            norm = re.sub(r"#.*|//.*", "", content)
            semantic_hash = hashlib.sha256(re.sub(r"\s+", "", norm).encode()).hexdigest()

        deterministic_id = hashlib.sha256(
            f"{project_id}:{file_path}:{name}:{semantic_hash}".encode()
        ).hexdigest()
        point_id = int(deterministic_id[:16], 16) % (2**63)
        client = self._ensure_client()
        await asyncio.to_thread(
            client.upsert,
            collection_name=COLLECTIONS["code"],
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "project_id": str(project_id),
                        "file_path": file_path,
                        "entry_type": entry_type,
                        "name": name,
                        "content": content,
                        "metadata": metadata,
                    },
                )
            ],
        )

    async def upsert_decision(
        self,
        project_id: UUID,
        decision_id: UUID,
        title: str,
        decision: str,
        reason: str,
        embedding: list[float],
    ) -> None:
        client = self._ensure_client()
        await asyncio.to_thread(
            client.upsert,
            collection_name=COLLECTIONS["decisions"],
            points=[
                PointStruct(
                    id=str(decision_id),
                    vector=embedding,
                    payload={
                        "project_id": str(project_id),
                        "title": title,
                        "decision": decision,
                        "reason": reason,
                    },
                )
            ],
        )

    async def upsert_bug(
        self,
        project_id: UUID,
        bug_id: UUID,
        title: str,
        problem: str,
        solution: str | None,
        embedding: list[float],
    ) -> None:
        client = self._ensure_client()
        await asyncio.to_thread(
            client.upsert,
            collection_name=COLLECTIONS["bugs"],
            points=[
                PointStruct(
                    id=str(bug_id),
                    vector=embedding,
                    payload={
                        "project_id": str(project_id),
                        "title": title,
                        "problem": problem,
                        "solution": solution,
                    },
                )
            ],
        )

    async def search_code(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        start_time = time.perf_counter()
        try:
            search_filter = self._build_filter(project_id, filters)
            client = self._ensure_client()
            results = await asyncio.to_thread(
                client.query_points,
                collection_name=COLLECTIONS["code"],
                query=query_embedding,
                query_filter=search_filter,
                limit=limit,
            )
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="code", status="success").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="code").observe(duration)
            return [{"id": h.id, "score": h.score, "payload": h.payload} for h in results.points]
        except Exception as e:
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="code", status="error").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="code").observe(duration)
            logger.error("vector_search_failed", collection="code", error=str(e))
            raise

    async def search_decisions(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        start_time = time.perf_counter()
        try:
            search_filter = self._build_project_filter(project_id)
            client = self._ensure_client()
            results = await asyncio.to_thread(
                client.query_points,
                collection_name=COLLECTIONS["decisions"],
                query=query_embedding,
                query_filter=search_filter,
                limit=limit,
            )
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="decisions", status="success").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="decisions").observe(duration)
            return [{"id": h.id, "score": h.score, "payload": h.payload} for h in results.points]
        except Exception as e:
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="decisions", status="error").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="decisions").observe(duration)
            logger.error("vector_search_failed", collection="decisions", error=str(e))
            raise

    async def search_bugs(
        self,
        query_embedding: list[float],
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        start_time = time.perf_counter()
        try:
            search_filter = self._build_project_filter(project_id)
            client = self._ensure_client()
            results = await asyncio.to_thread(
                client.query_points,
                collection_name=COLLECTIONS["bugs"],
                query=query_embedding,
                query_filter=search_filter,
                limit=limit,
            )
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="bugs", status="success").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="bugs").observe(duration)
            return [{"id": h.id, "score": h.score, "payload": h.payload} for h in results.points]
        except Exception as e:
            duration = time.perf_counter() - start_time
            VECTOR_SEARCH_CALLS.labels(collection="bugs", status="error").inc()
            VECTOR_SEARCH_LATENCY.labels(collection="bugs").observe(duration)
            logger.error("vector_search_failed", collection="bugs", error=str(e))
            raise

    async def delete_by_project(self, project_id: UUID) -> None:
        client = self._ensure_client()
        project_filter = Filter(
            must=[FieldCondition(key="project_id", match=MatchValue(value=str(project_id)))]
        )
        for collection_name in COLLECTIONS.values():
            await asyncio.to_thread(
                client.delete,
                collection_name=collection_name,
                points_selector=project_filter,
            )

    async def delete_by_file(self, project_id: UUID, file_path: str) -> None:
        client = self._ensure_client()
        file_filter = Filter(
            must=[
                FieldCondition(key="project_id", match=MatchValue(value=str(project_id))),
                FieldCondition(key="file_path", match=MatchValue(value=file_path)),
            ]
        )
        await asyncio.to_thread(
            client.delete,
            collection_name=COLLECTIONS["code"],
            points_selector=file_filter,
        )

    def _build_filter(
        self, project_id: UUID | None, additional_filters: dict[str, str] | None = None
    ) -> Filter | None:
        must_conditions = []
        if project_id is not None:
            must_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=str(project_id)))
            )

        if additional_filters:
            for key, value in additional_filters.items():
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        if not must_conditions:
            return None

        return Filter(must=must_conditions)  # type: ignore

    def _build_project_filter(self, project_id: UUID | None) -> Filter | None:
        if project_id is None:
            return None
        return Filter(
            must=[FieldCondition(key="project_id", match=MatchValue(value=str(project_id)))]
        )


vector_store = QdrantVectorStore()
