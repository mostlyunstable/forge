"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.database.connection import database_manager
from forge.config.settings import get_settings


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session."""
    async with database_manager.get_session() as session:
        yield session


def get_vector_store() -> Any:
    """Return the appropriate vector store based on settings."""
    settings = get_settings()
    if settings.USE_QDRANT:
        from forge.infrastructure.search.qdrant_client import vector_store
        return vector_store
    from forge.infrastructure.search.in_memory_vector_store import in_memory_vector_store
    return in_memory_vector_store
