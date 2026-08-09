"""Shared FastAPI dependencies."""

from __future__ import annotations

import os
import secrets
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from forge.config.settings import get_settings
from forge.infrastructure.database.connection import database_manager

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

def verify_auth_token(
    api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    expected_token = os.environ.get("FORGE_API_KEY")
    if not expected_token:
        return

    actual_token = api_key or (bearer.credentials if bearer else None)
    if not actual_token or not secrets.compare_digest(actual_token, expected_token):
        raise HTTPException(status_code=401, detail="Invalid authentication token")


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
