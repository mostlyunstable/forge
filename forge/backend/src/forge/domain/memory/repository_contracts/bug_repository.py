"""IBugRepository - contract for bug persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.projects.value_objects.project_id import ProjectId


class IBugRepository(ABC):
    """Interface for bug persistence."""

    @abstractmethod
    async def get_by_id(self, bug_id: BugId) -> Optional[Bug]:
        """Retrieve a bug by its ID."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> list[Bug]:
        """Retrieve all bugs for a project, newest first."""

    @abstractmethod
    async def get_unresolved(self, project_id: ProjectId) -> list[Bug]:
        """Retrieve unresolved bugs for a project."""

    @abstractmethod
    async def save(self, bug: Bug) -> Bug:
        """Persist a new or updated bug."""

    @abstractmethod
    async def delete(self, bug_id: BugId) -> bool:
        """Delete a bug by ID."""

    @abstractmethod
    async def search_by_problem(self, query: str) -> list[Bug]:
        """Search bugs by problem description."""
