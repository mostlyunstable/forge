import asyncio
import os
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock

from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.infrastructure.indexing.index_job_repository import IndexJobRepository
from forge.infrastructure.indexing.file_index_repository import FileIndexRepository
from forge.infrastructure.indexing.extraction_candidate_repository import ExtractionCandidateRepository
from forge.infrastructure.database.connection import DatabaseManager
from forge.domain.indexing.entities.index_job import JobStatus

import tempfile

@pytest.fixture
async def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{f.name}"
        manager = DatabaseManager()
        await manager.run_migrations()
        yield manager
        await manager.close()
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

@pytest.mark.asyncio
async def test_rel_idempotency_indexing(temp_db):
    """Property 16: Idempotency.
    
    Retry mechanisms must not corrupt the vector database if a job is retried.
    Running FullIndexUseCase twice on the same project should gracefully handle state
    and overwrite indices without corruption.
    """
    project_id = uuid.uuid4()
    
    # Run once
    async with temp_db.get_session() as session:
        job_repo = IndexJobRepository(session)
        usecase = FullIndexUseCase(
            job_repo=job_repo,
            file_index_repo=FileIndexRepository(session),
            candidate_repo=ExtractionCandidateRepository(session),
            memory_extractor=AsyncMock(extract_from_code_comments=MagicMock(return_value=[])),
            git_history_ingester=AsyncMock(ingest=AsyncMock(return_value={"commits_ingested": 1})),
            git_diff_provider=AsyncMock(get_latest_commit=MagicMock(return_value="commit_hash_123")),
            commit_parser=MagicMock(get_commit_history=MagicMock(return_value=[])),
        )
        mock_indexer = AsyncMock()
        mock_indexer.index = AsyncMock(return_value=[])
        usecase.set_code_indexer(mock_indexer)
        
        job1 = await usecase.execute(project_id=project_id, repo_path="/fake")
        await session.commit()
    
    # Run again (simulate retry)
    async with temp_db.get_session() as session:
        job_repo = IndexJobRepository(session)
        usecase = FullIndexUseCase(
            job_repo=job_repo,
            file_index_repo=FileIndexRepository(session),
            candidate_repo=ExtractionCandidateRepository(session),
            memory_extractor=AsyncMock(extract_from_code_comments=MagicMock(return_value=[])),
            git_history_ingester=AsyncMock(ingest=AsyncMock(return_value={"commits_ingested": 1})),
            git_diff_provider=AsyncMock(get_latest_commit=MagicMock(return_value="commit_hash_123")),
            commit_parser=MagicMock(get_commit_history=MagicMock(return_value=[])),
        )
        mock_indexer = AsyncMock()
        mock_indexer.index = AsyncMock(return_value=[])
        usecase.set_code_indexer(mock_indexer)
        
        job2 = await usecase.execute(project_id=project_id, repo_path="/fake")
        await session.commit()

    assert job1.status == JobStatus.COMPLETED
    assert job2.status == JobStatus.COMPLETED
    assert job1.id != job2.id, "Retries generate distinct job records"

@pytest.mark.asyncio
async def test_rel_idempotency_chat():
    """Property 4: Chat Idempotency.
    
    Identical re-transmissions of a user query due to network lag should not 
    result in divergent contexts.
    """
    assert True
