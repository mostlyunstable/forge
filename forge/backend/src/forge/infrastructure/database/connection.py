"""Database connection and session management."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from forge.config.settings import get_settings
from forge.infrastructure.database.base import Base


class DatabaseManager:
    """Manages database engine and session lifecycle."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def _ensure_engine(self) -> AsyncEngine:
        if self._engine is None:
            kwargs = {
                "echo": self._settings.DEBUG,
            }
            if "postgresql" in self._settings.DATABASE_URL:
                kwargs["pool_size"] = 20
                kwargs["max_overflow"] = 10
            self._engine = create_async_engine(
                self._settings.DATABASE_URL,
                **kwargs,
            )
        return self._engine

    def _ensure_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self._ensure_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory

    async def init_db(self) -> None:
        """Create all tables. Used at startup."""
        engine = self._ensure_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional session scope."""
        factory = self._ensure_session_factory()
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Dispose of the engine."""
        if self._engine:
            await self._engine.dispose()


database_manager = DatabaseManager()
