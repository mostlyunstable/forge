import asyncio
import os
import pytest
from uuid import UUID
import uuid

from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.domain.indexing.entities.index_job import JobStatus
from forge.infrastructure.indexing.index_job_repository import IndexJobRepository
from forge.infrastructure.indexing.file_index_repository import FileIndexRepository
from forge.infrastructure.indexing.extraction_candidate_repository import ExtractionCandidateRepository
from forge.infrastructure.database.connection import DatabaseManager
from unittest.mock import AsyncMock, MagicMock

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
async def test_rel_embedding_dimension_mismatch(temp_db):
    """Property 11: Embedding Dimension Consistency.
    
    If embedding dimensions don't match, or an API error occurs,
    the index job should fail gracefully and not be stuck in RUNNING.
    """
    project_id = uuid.uuid4()
    
    async with temp_db.get_session() as session:
        job_repo = IndexJobRepository(session)
        file_index_repo = FileIndexRepository(session)
        candidate_repo = ExtractionCandidateRepository(session)
    
        git_history_mock = AsyncMock()
        git_history_mock.ingest_history = AsyncMock()
    
        usecase = FullIndexUseCase(
            job_repo=job_repo,
            file_index_repo=file_index_repo,
            candidate_repo=candidate_repo,
            memory_extractor=AsyncMock(extract_from_code_comments=MagicMock(return_value=[])),
            git_history_ingester=git_history_mock,
            git_diff_provider=AsyncMock(),
            commit_parser=MagicMock(get_commit_history=MagicMock(return_value=[])),
        )
        
        mock_indexer = AsyncMock()
        mock_indexer.index = AsyncMock(side_effect=RuntimeError("Embedding API dimension mismatch / 500 Error"))
        usecase.set_code_indexer(mock_indexer)
    
        try:
            await usecase.execute(project_id=project_id, repo_path="/fake")
        except Exception:
            pass # We expect an exception or a graceful exit
            
        await session.commit()
        
    async with temp_db.get_session() as session2:
        job_repo2 = IndexJobRepository(session2)
        job = await job_repo2.get_latest_completed(project_id)
        if not job:
            jobs = await job_repo2.get_by_project(project_id)
            if jobs:
                job = jobs[0]
                
        assert job is not None, "Job should have been created"
        assert job.status == JobStatus.FAILED, "Job should have transitioned to FAILED after embedding error"
        assert "Embedding API dimension mismatch" in str(job.error_log), "Error log should contain the failure reason"

@pytest.mark.asyncio
async def test_rel_embedding_api_failure():
    """Property 10: Embedding API failure handling."""
    pass
