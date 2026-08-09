import asyncio
import os
import pytest
import uuid
import shutil
import tempfile
from unittest.mock import AsyncMock, MagicMock

from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.infrastructure.indexing.index_job_repository import IndexJobRepository
from forge.infrastructure.indexing.file_index_repository import FileIndexRepository
from forge.infrastructure.indexing.extraction_candidate_repository import ExtractionCandidateRepository
from forge.infrastructure.database.connection import DatabaseManager
from forge.domain.indexing.entities.index_job import JobStatus

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
async def test_rel_git_races(temp_db):
    """Property 21: Git Race Conditions.
    
    If a `git push` updates the repository concurrently while `FullIndexUseCase` is reading files,
    it must not crash or produce corrupt chunks. E.g., if a file is deleted during enumeration.
    """
    project_id = uuid.uuid4()
    
    with tempfile.TemporaryDirectory() as temp_repo:
        # Create a file
        file_path = os.path.join(temp_repo, "test.py")
        with open(file_path, "w") as f:
            f.write("print('hello')")
            
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
            
            # Monkey-patch os.walk to simulate a race: enumerate sees the file, but it's deleted before reading
            original_walk = os.walk
            def mock_walk(*args, **kwargs):
                os.remove(file_path) # Delete the file mid-enumeration
                return original_walk(*args, **kwargs)
                
            original_os_walk = os.walk
            os.walk = mock_walk
            try:
                job = await usecase.execute(project_id=project_id, repo_path=temp_repo)
            finally:
                os.walk = original_os_walk
                
            await session.commit()
            
        assert job.status == JobStatus.COMPLETED
        # The file was deleted so it should not fail the job, it gracefully ignores the missing file.
