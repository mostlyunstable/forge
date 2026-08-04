"""ICodeRepository - contract for code entry persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.projects.value_objects.project_id import ProjectId


class ICodeRepository(ABC):
    """Interface for code entry persistence."""

    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> CodeEntry | None:
        """Retrieve a code entry by its UUID."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> list[CodeEntry]:
        """Retrieve all code entries for a project, ordered by file path."""

    @abstractmethod
    async def get_by_file_path(self, project_id: ProjectId, file_path: str) -> list[CodeEntry]:
        """Retrieve all entries in a specific file, ordered by line number."""

    @abstractmethod
    async def get_by_type(self, project_id: ProjectId, entry_type: EntryType) -> list[CodeEntry]:
        """Retrieve all entries of a specific type for a project."""

    @abstractmethod
    async def save_many(self, entries: list[CodeEntry]) -> list[CodeEntry]:
        """Persist multiple code entries at once."""

    @abstractmethod
    async def delete_by_project(self, project_id: ProjectId) -> bool:
        """Delete all entries for a project (used during re-indexing)."""

    @abstractmethod
    async def search_by_name(self, project_id: ProjectId, query: str) -> list[CodeEntry]:
        """Search entries by name substring."""
