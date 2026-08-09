import pytest
import uuid
import asyncio
from unittest.mock import AsyncMock, patch

from forge.application.indexing.incremental_index_usecase import (
    IncrementalIndexUseCase,
)
from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.value_objects.job_status import JobStatus
from forge.domain.projects.entities.project import Project

@pytest.fixture
def mock_code_indexer():
    mock = AsyncMock()
    # Return some fake nodes to index
    mock.incremental_index.return_value = {"nodes_added": 10}
    return mock

@pytest.fixture
def index_job_repo():
    class FakeRepo:
        def __init__(self):
            self.jobs = {}
        async def save(self, job):
            self.jobs[job.id] = job
        async def get_by_id(self, id):
            return self.jobs.get(id)
        async def get_latest_completed(self, project_id):
            job = IndexJob.create(project_id=project_id, type="full")
            job.state_hash = "old_hash"
            job.save_checkpoint({"last_commit_sha": "commit_123"})
            return job
    return FakeRepo()

@pytest.fixture
def project_repo():
    class FakeProjRepo:
        def __init__(self):
            self.proj = Project.create(name="test", description="desc", stack="python")
            self.proj.state_hash = "old_hash"
        async def get_by_id(self, id):
            return self.proj
        async def save(self, proj):
            self.proj = proj
    return FakeProjRepo()

@pytest.mark.asyncio
async def test_rel_incremental_indexing_failure(
    mock_code_indexer, index_job_repo, project_repo, tmp_path
):
    """Property 5, 9, 20: Incremental Indexing Failure.
    
    If the incremental indexer crashes mid-way, the project's state_hash should NOT be updated.
    The job should be marked as FAILED and the error should be logged.
    """
    # Create a real temp file
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    file1 = repo_path / "file1.py"
    file1.write_text("print('hello')")
    
    from unittest.mock import MagicMock
    git_diff_mock = MagicMock()
    git_diff_mock.get_latest_commit.return_value = "commit_123"
    git_diff_mock.get_changed_files.return_value = [{"file_path": "file1.py", "change_type": "M"}]
    
    commit_mock = MagicMock()
    commit_mock.get_commit_history.return_value = []
    
    usecase = IncrementalIndexUseCase(
        job_repo=index_job_repo,
        file_index_repo=AsyncMock(get_by_project_and_path=AsyncMock(return_value=None)),
        candidate_repo=AsyncMock(),
        memory_extractor=AsyncMock(extract_from_code_comments=MagicMock(return_value=[])),
        git_diff_provider=git_diff_mock,
        commit_parser=commit_mock,
    )
    usecase.set_code_indexer(mock_code_indexer)
    
    # Simulate a crash during code indexing
    mock_code_indexer.index_files = AsyncMock(side_effect=RuntimeError("Qdrant incremental crash"))
    
    proj_id = project_repo.proj.id
    
    with pytest.raises(RuntimeError):
        await usecase.execute(project_id=proj_id, repo_path=str(repo_path))
        
    # Find the job that was created
    assert len(index_job_repo.jobs) == 1
    job = list(index_job_repo.jobs.values())[0]
    
    assert job.status == JobStatus.FAILED
    assert len(job.error_log) > 0
    assert "Qdrant incremental crash" in job.error_log[0]["error"]
    
    # Verify the project's state hash did NOT update, so it will retry next time
    proj = await project_repo.get_by_id(proj_id)
    assert proj.state_hash == "old_hash", "Project state_hash updated despite job failure!"
