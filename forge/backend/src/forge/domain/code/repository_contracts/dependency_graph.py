"""IDependencyGraph - contract for dependency graph operations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from forge.domain.code.value_objects.dependency_edge import DependencyEdge
from forge.domain.projects.value_objects.project_id import ProjectId


class IDependencyGraph(ABC):
    """Interface for dependency graph analysis. Implementations live in infrastructure."""

    @abstractmethod
    async def build(self, project_id: ProjectId, indexed_files: list[dict[str, Any]]) -> None:
        """Build dependency graph from indexed file data."""

    @abstractmethod
    async def get_imports(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get direct imports from a file."""

    @abstractmethod
    async def get_dependents(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get files that import this file."""

    @abstractmethod
    async def get_transitive_imports(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get all transitive imports."""

    @abstractmethod
    async def get_reverse_transitive(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get all reverse transitive dependents."""

    @abstractmethod
    async def detect_cycles(self, project_id: ProjectId) -> list[list[str]]:
        """Detect circular dependencies."""

    @abstractmethod
    async def get_statistics(self, project_id: ProjectId) -> dict[str, Any]:
        """Get graph statistics."""
