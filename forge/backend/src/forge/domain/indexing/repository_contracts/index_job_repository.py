"""IIndexJobRepository — persistence port for IndexJob aggregate."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from forge.domain.indexing.entities.index_job import IndexJob


class IIndexJobRepository(ABC):
    """Interface for IndexJob persistence."""

    @abstractmethod
    async def save(self, job: IndexJob) -> IndexJob:
        """Persist an index job."""

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> IndexJob | None:
        """Retrieve an index job by ID."""

    @abstractmethod
    async def get_by_project(
        self, project_id: UUID, limit: int = 20, skip: int = 0
    ) -> list[IndexJob]:
        """Retrieve index jobs for a project."""

    @abstractmethod
    async def get_latest_completed(self, project_id: UUID) -> IndexJob | None:
        """Get the most recently completed index job for a project."""

    @abstractmethod
    async def get_running(self, project_id: UUID) -> IndexJob | None:
        """Get the currently running index job for a project, if any."""
