"""IProjectRepository - contract for project persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId


class IProjectRepository(ABC):
    """Interface for project persistence. Implementations live in infrastructure."""

    @abstractmethod
    async def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Retrieve a project by its ID."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Project]:
        """Retrieve a project by its unique name."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Project]:
        """Retrieve all projects with pagination."""

    @abstractmethod
    async def save(self, project: Project) -> Project:
        """Persist a new or updated project."""

    @abstractmethod
    async def delete(self, project_id: ProjectId) -> bool:
        """Delete a project by ID. Returns True if deleted."""

    @abstractmethod
    async def search_by_name(self, query: str) -> list[Project]:
        """Search projects by name substring."""
