"""ICommitRepository - contract for commit persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.git.entities.commit import Commit
from forge.domain.git.value_objects.commit_classification import CommitClassification
from forge.domain.git.value_objects.commit_sha import CommitSha
from forge.domain.projects.value_objects.project_id import ProjectId


class ICommitRepository(ABC):
    """Interface for commit persistence."""

    @abstractmethod
    async def get_by_sha(self, project_id: ProjectId, sha: CommitSha) -> Optional[Commit]:
        """Retrieve a commit by its SHA."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> list[Commit]:
        """Retrieve all commits for a project, newest first."""

    @abstractmethod
    async def get_by_classification(
        self, project_id: ProjectId, classification: CommitClassification
    ) -> list[Commit]:
        """Retrieve commits filtered by classification."""

    @abstractmethod
    async def get_recent(self, project_id: ProjectId, limit: int = 10) -> list[Commit]:
        """Retrieve the most recent commits for a project."""

    @abstractmethod
    async def save(self, commit: Commit) -> Commit:
        """Persist a new commit."""

    @abstractmethod
    async def save_many(self, commits: list[Commit]) -> list[Commit]:
        """Persist multiple commits at once."""
