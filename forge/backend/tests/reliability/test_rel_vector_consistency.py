import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
import os
from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.application.indexing.full_index_usecase import FullIndexUseCase
from qdrant_client.http.exceptions import UnexpectedResponse

@pytest.fixture
def index_job_repo():
    class FakeJobRepo:
        def __init__(self):
            self.jobs = {}
        async def save(self, job):
            self.jobs[job.id] = job
        async def save_many(self, jobs):
            pass
    return FakeJobRepo()

@pytest.fixture
def file_index_repo():
    class FakeFileRepo:
        async def save_many(self, files):
            pass
    return FakeFileRepo()

@pytest.mark.asyncio
async def test_rel_vector_consistency_qdrant_upsert_failure(index_job_repo, file_index_repo):
    """Property 7 & 8: Qdrant Failure and Database/Vector Consistency."""
    
    # We will simulate a failure during the upsert_code_chunks or equivalent
    # We will mock CodeIndexer.index to throw an exception that would come from Qdrant
    code_indexer = MagicMock()
    code_indexer.index = AsyncMock(side_effect=RuntimeError("Simulated Qdrant Network Failure"))
    
    use_case = FullIndexUseCase(
        job_repo=index_job_repo,
        file_index_repo=file_index_repo,
        candidate_repo=MagicMock(),
        memory_extractor=MagicMock(),
        git_history_ingester=MagicMock(),
        git_diff_provider=MagicMock(),
        commit_parser=MagicMock(),
    )
    use_case.set_code_indexer(code_indexer)
    
    proj_id = uuid.uuid4()
    
    with pytest.raises(RuntimeError):
        # We need a real directory to enumerate files on, even just an empty one or temporary
        await use_case.execute(proj_id, "/tmp")
        
    # Now verify the job state. Did it get marked as FAILED?
    job = list(index_job_repo.jobs.values())[0]
    
    assert job.status.value == "failed", f"Job status is {job.status}, expected FAILED."
    assert len(job.error_log) > 0, "No error log was recorded."
    assert "Simulated Qdrant Network Failure" in job.error_log[0]["error"], "Error message not recorded."
