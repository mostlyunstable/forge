"""Schemas for indexing API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class StartIndexRequest(BaseModel):
    """Request to start an indexing job."""

    project_id: str = Field(..., description="Project ID to index")
    repo_path: str = Field(..., description="Path to the git repository")
    type: str = Field(default="full", description="Index type: full, incremental, git_only, memory_only")


class IndexJobResponse(BaseModel):
    """Response for an indexing job."""

    id: str
    project_id: str
    type: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    progress: dict = {}
    result: dict = {}
    error_log: list[dict] = []
    state_hash: str = ""
    created_by: str = "api"
    created_at: str
    duration_seconds: float | None = None


class ListIndexJobsResponse(BaseModel):
    """Response for listing indexing jobs."""

    jobs: list[IndexJobResponse]
    total: int
    project_id: str


class ExtractionCandidateResponse(BaseModel):
    """Response for an extraction candidate."""

    id: str
    job_id: str
    kind: str
    confidence: float
    status: str
    data: dict = {}
    source_commit: str = ""
    source_file: str = ""
    created_at: str


class IndexStatusResponse(BaseModel):
    """Current indexing status for a project."""

    project_id: str
    total_files_indexed: int
    last_index_job: IndexJobResponse | None = None
    running_job: IndexJobResponse | None = None
    candidates_by_kind: dict[str, int] = {}
