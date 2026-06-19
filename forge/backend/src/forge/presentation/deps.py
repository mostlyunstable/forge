"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import AsyncGenerator, Any

from fastapi import Depends
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


def get_project_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.project_repository import ProjectRepository
    return ProjectRepository(session)


def get_decision_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.decision_repository import DecisionRepository
    return DecisionRepository(session)


def get_bug_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.bug_repository import BugRepository
    return BugRepository(session)


def get_preference_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.preference_repository import PreferenceRepository
    return PreferenceRepository(session)


def get_code_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.code_repository import CodeRepository
    return CodeRepository(session)


def get_commit_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.repositories.commit_repository import CommitRepository
    return CommitRepository(session)


def get_analysis_report_repo(session: AsyncSession = Depends(get_session)):
    from forge.infrastructure.analysis.analysis_repository import AnalysisReportRepository
    return AnalysisReportRepository(session)
