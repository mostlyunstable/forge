"""IExtractionCandidateRepository — persistence port for ExtractionCandidate."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from forge.domain.indexing.entities.extraction_candidate import ExtractionCandidate


class IExtractionCandidateRepository(ABC):
    """Interface for ExtractionCandidate persistence."""

    @abstractmethod
    async def save(self, candidate: ExtractionCandidate) -> ExtractionCandidate:
        """Persist an extraction candidate."""

    @abstractmethod
    async def save_many(self, candidates: list[ExtractionCandidate]) -> int:
        """Persist multiple candidates. Returns count saved."""

    @abstractmethod
    async def get_by_id(self, candidate_id: UUID) -> ExtractionCandidate | None:
        """Get a candidate by ID."""

    @abstractmethod
    async def get_by_dedup_key(self, dedup_key: str) -> ExtractionCandidate | None:
        """Check if a candidate with this dedup key already exists."""

    @abstractmethod
    async def get_by_job(self, job_id: UUID) -> list[ExtractionCandidate]:
        """Get all candidates from a specific job."""

    @abstractmethod
    async def get_pending_review(
        self, project_id: UUID, limit: int = 50
    ) -> list[ExtractionCandidate]:
        """Get candidates that need human review (suggested status)."""

    @abstractmethod
    async def get_accepted(
        self, project_id: UUID, kind: str | None = None
    ) -> list[ExtractionCandidate]:
        """Get accepted candidates, optionally filtered by kind."""

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> dict[str, int]:
        """Count candidates by kind for a project."""
