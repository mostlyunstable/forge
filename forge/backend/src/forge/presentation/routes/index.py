"""Index routes — codebase indexing API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.indexing.index_job_repository import IndexJobRepository
from forge.infrastructure.indexing.file_index_repository import FileIndexRepository
from forge.infrastructure.indexing.extraction_candidate_repository import (
    ExtractionCandidateRepository,
)
from forge.infrastructure.git.git_diff_parser import GitDiffParser
from forge.infrastructure.git.commit_parser import CommitParser
from forge.infrastructure.search.embedding_service import EmbeddingService
from forge.infrastructure.search.in_memory_vector_store import in_memory_vector_store
from forge.application.indexing.memory_extractor import MemoryExtractor
from forge.application.indexing.git_history_ingester import GitHistoryIngester
from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.application.indexing.incremental_index_usecase import IncrementalIndexUseCase
from forge.application.indexing.reindex_detector import ReindexDetector
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.index_schemas import (
    StartIndexRequest,
    IndexJobResponse,
    ListIndexJobsResponse,
    IndexStatusResponse,
)

router = APIRouter(prefix="/index", tags=["indexing"])


def _build_full_index_use_case(session: AsyncSession) -> FullIndexUseCase:
    """Build FullIndexUseCase with all dependencies."""
    job_repo = IndexJobRepository(session)
    file_index_repo = FileIndexRepository(session)
    candidate_repo = ExtractionCandidateRepository(session)
    memory_extractor = MemoryExtractor()
    commit_parser = CommitParser()
    git_diff_parser = GitDiffParser()
    git_ingester = GitHistoryIngester(job_repo, commit_parser, memory_extractor)
    embedding_service = EmbeddingService()
    vector_store = in_memory_vector_store

    return FullIndexUseCase(
        job_repo=job_repo,
        file_index_repo=file_index_repo,
        candidate_repo=candidate_repo,
        memory_extractor=memory_extractor,
        git_history_ingester=git_ingester,
        git_diff_provider=git_diff_parser,
        commit_parser=commit_parser,
        vector_store=vector_store,
        embedding_service=embedding_service,
    )


def _build_incremental_index_use_case(session: AsyncSession) -> IncrementalIndexUseCase:
    """Build IncrementalIndexUseCase with all dependencies."""
    job_repo = IndexJobRepository(session)
    file_index_repo = FileIndexRepository(session)
    candidate_repo = ExtractionCandidateRepository(session)
    memory_extractor = MemoryExtractor()
    commit_parser = CommitParser()
    git_diff_parser = GitDiffParser()

    return IncrementalIndexUseCase(
        job_repo=job_repo,
        file_index_repo=file_index_repo,
        candidate_repo=candidate_repo,
        memory_extractor=memory_extractor,
        git_diff_provider=git_diff_parser,
        commit_parser=commit_parser,
    )


@router.post("/jobs", response_model=IndexJobResponse, status_code=201)
async def start_index_job(
    body: StartIndexRequest,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """Start an indexing job for a project."""
    # Verify project exists
    from uuid import UUID
    from forge.domain.projects.value_objects.project_id import ProjectId
    project_repo = ProjectRepository(session)
    try:
        pid = ProjectId(UUID(body.project_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    project = await project_repo.get_by_id(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for running jobs
    job_repo = IndexJobRepository(session)
    running = await job_repo.get_running(UUID(body.project_id))
    if running:
        raise HTTPException(
            status_code=409,
            detail=f"Index job already running: {running.id}",
        )

    # Build and run appropriate use case
    if body.type == "full" or body.type == "incremental":
        # Check if full index is needed
        file_index_repo = FileIndexRepository(session)
        detector = ReindexDetector(job_repo, file_index_repo)
        # For now, always run requested type
        if body.type == "full":
            use_case = _build_full_index_use_case(session)
            job = await use_case.execute(
                project_id=UUID(body.project_id),
                repo_path=body.repo_path,
                created_by="api",
            )
        else:
            use_case = _build_incremental_index_use_case(session)
            job = await use_case.execute(
                project_id=UUID(body.project_id),
                repo_path=body.repo_path,
                created_by="api",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Index type '{body.type}' not yet supported",
        )

    return _job_to_response(job)


@router.get("/jobs", response_model=ListIndexJobsResponse)
async def list_index_jobs(
    project_id: str,
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """List indexing jobs for a project."""
    from uuid import UUID
    job_repo = IndexJobRepository(session)
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    jobs = await job_repo.get_by_project(pid, skip=skip, limit=limit)
    return ListIndexJobsResponse(
        jobs=[_job_to_response(j) for j in jobs],
        total=len(jobs),
        project_id=project_id,
    )


@router.get("/jobs/{job_id}", response_model=IndexJobResponse)
async def get_index_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """Get a specific indexing job."""
    from uuid import UUID
    job_repo = IndexJobRepository(session)
    try:
        job = await job_repo.get_by_id(UUID(job_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    if not job:
        raise HTTPException(status_code=404, detail="Index job not found")
    return _job_to_response(job)


@router.get("/status/{project_id}", response_model=IndexStatusResponse)
async def get_index_status(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """Get current indexing status for a project."""
    from uuid import UUID
    job_repo = IndexJobRepository(session)
    file_index_repo = FileIndexRepository(session)
    candidate_repo = ExtractionCandidateRepository(session)

    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    total_files = await file_index_repo.count_by_project(pid)
    last_job = await job_repo.get_latest_completed(pid)
    running_job = await job_repo.get_running(pid)
    candidates = await candidate_repo.count_by_project(pid)

    return IndexStatusResponse(
        project_id=project_id,
        total_files_indexed=total_files,
        last_index_job=_job_to_response(last_job) if last_job else None,
        running_job=_job_to_response(running_job) if running_job else None,
        candidates_by_kind=candidates,
    )


def _job_to_response(job) -> IndexJobResponse:
    """Convert IndexJob to response schema."""
    return IndexJobResponse(
        id=str(job.id),
        project_id=str(job.project_id),
        type=job.type.value,
        status=job.status.value,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        progress=job.progress,
        result=job.result,
        error_log=job.error_log,
        state_hash=job.state_hash,
        created_by=job.created_by,
        created_at=job.created_at.isoformat(),
        duration_seconds=job.duration_seconds,
    )
