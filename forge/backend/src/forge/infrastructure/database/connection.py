"""Database connection and session management."""

from __future__ import annotations

import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from forge.config.settings import get_settings


class DatabaseManager:
    """Manages database engine and session lifecycle."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def _ensure_engine(self) -> AsyncEngine:
        if self._engine is None:
            is_sqlite = "sqlite" in self._settings.DATABASE_URL
            kwargs: dict = {
                "echo": self._settings.DEBUG,
            }
            if is_sqlite:
                # Use NullPool for SQLite to avoid cross-thread/cross-coroutine
                # connection reuse which causes "database is locked" errors.
                from sqlalchemy.pool import NullPool

                kwargs["poolclass"] = NullPool
                kwargs["connect_args"] = {"check_same_thread": False}
            elif "postgresql" in self._settings.DATABASE_URL:
                kwargs["pool_size"] = 20
                kwargs["max_overflow"] = 10
            self._engine = create_async_engine(
                self._settings.DATABASE_URL,
                **kwargs,
            )

            if is_sqlite:
                from sqlalchemy import event

                @event.listens_for(self._engine.sync_engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.close()

        return self._engine

    def _ensure_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self._ensure_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory

    async def run_migrations(self) -> None:
        """Apply Alembic migrations to bring the schema up to date.

        This is the recommended way to initialise the database at startup.
        It runs ``alembic upgrade head`` programmatically.
        """
        from alembic.config import Config

        from alembic import command

        alembic_cfg = Config("alembic.ini")
        # Override the URL with the runtime setting so env.py picks it up.
        alembic_cfg.set_main_option("sqlalchemy.url", self._settings.DATABASE_URL)

        # Run migrations in a thread since alembic.command is synchronous.
        import asyncio

        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    async def init_db(self) -> None:
        """Create all tables directly (legacy).

        .. deprecated::
            Use :meth:`run_migrations` instead.  ``init_db`` is kept for
            backward compatibility with tests that create fresh databases
            and do not want to depend on Alembic.
        """
        warnings.warn(
            "DatabaseManager.init_db() is deprecated. Use run_migrations() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from forge.infrastructure.database.base import Base

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
