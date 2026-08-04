"""IFileIndexRepository — persistence port for FileIndex."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from forge.domain.indexing.entities.file_index import FileIndex


class IFileIndexRepository(ABC):
    """Interface for FileIndex persistence."""

    @abstractmethod
    async def save(self, file_index: FileIndex) -> FileIndex:
        """Persist a file index entry."""

    @abstractmethod
    async def save_many(self, file_indices: list[FileIndex]) -> int:
        """Persist multiple file index entries. Returns count saved."""

    @abstractmethod
    async def get_by_project_and_path(self, project_id: UUID, file_path: str) -> FileIndex | None:
        """Get a file index by project and path."""

    @abstractmethod
    async def get_by_project(self, project_id: UUID) -> list[FileIndex]:
        """Get all file indices for a project."""

    @abstractmethod
    async def get_stale_files(
        self, project_id: UUID, current_hashes: dict[str, str]
    ) -> list[FileIndex]:
        """Get files whose content hash differs from current_hashes."""

    @abstractmethod
    async def delete_by_project(self, project_id: UUID) -> int:
        """Delete all file indices for a project. Returns count deleted."""

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        """Count files indexed for a project."""
