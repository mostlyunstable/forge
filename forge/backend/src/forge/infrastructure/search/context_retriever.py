"""Context retriever adapter — bridges use case port to vector infrastructure."""
from __future__ import annotations

from typing import Any

from forge.infrastructure.search.embedding_service import EmbeddingService


class ContextRetriever:
    """Adapter that implements IContextRetriever using vector store."""

    def __init__(self, vector_store: Any = None) -> None:
        self._embedding_service = EmbeddingService()
        self._vector_store = vector_store

    async def retrieve(self, query: str, project_id) -> dict:
        query_embedding = await self._embedding_service.get_embedding(query)
        project_uuid = project_id.value if hasattr(project_id, "value") else project_id
        code = await self._vector_store.search_code(query_embedding, project_uuid, limit=5)
        decisions = await self._vector_store.search_decisions(query_embedding, project_uuid, limit=5)
        bugs = await self._vector_store.search_bugs(query_embedding, project_uuid, limit=3)
        return {
            "relevant_code": code,
            "relevant_decisions": decisions,
            "relevant_bugs": bugs,
        }
