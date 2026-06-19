"""IDependencyRepository - contract for dependency persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod

from forge.domain.code.entities.code_dependency import CodeDependency
from forge.domain.projects.value_objects.project_id import ProjectId


class IDependencyRepository(ABC):
    """Interface for dependency persistence. Implementations live in infrastructure."""

    @abstractmethod
    async def save_batch(self, dependencies: list[CodeDependency]) -> None:
        """Persist a batch of dependencies."""

    @abstractmethod
    async def find_by_source(self, project_id: ProjectId, file_path: str) -> list[CodeDependency]:
        """Find all dependencies originating from a file."""

    @abstractmethod
    async def find_by_target(self, project_id: ProjectId, file_path: str) -> list[CodeDependency]:
        """Find all dependencies targeting a file."""

    @abstractmethod
    async def find_all(self, project_id: ProjectId) -> list[CodeDependency]:
        """Find all dependencies for a project."""

    @abstractmethod
    async def delete_by_project(self, project_id: ProjectId) -> None:
        """Delete all dependencies for a project."""
