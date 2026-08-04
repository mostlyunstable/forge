"""Ports for PR analysis — interfaces the application layer depends on."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from forge.domain.projects.value_objects.project_id import ProjectId


class IDiffProvider(ABC):
    """Provides git diff data for a PR or commit range."""

    @abstractmethod
    async def get_pr_diff(self, project_id: ProjectId, pr_number: int) -> dict[str, Any]:
        """Get the diff for a pull request.

        Returns:
            dict with keys:
                - title: str
                - body: str
                - files: list[dict] with file_path, change_type, additions, deletions
                - base_sha: str
                - head_sha: str
        """

    @abstractmethod
    async def get_commit_diff(
        self, project_id: ProjectId, base_sha: str, head_sha: str
    ) -> dict[str, Any]:
        """Get the diff between two commits.

        Returns same structure as get_pr_diff.
        """


class IContextSearcher(ABC):
    """Searches historical context related to changes."""

    @abstractmethod
    async def search_related_decisions(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Find decisions relevant to the given query."""

    @abstractmethod
    async def search_related_bugs(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Find bugs relevant to the given query."""

    @abstractmethod
    async def search_related_commits(
        self, project_id: str, file_paths: list[str], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find commits that previously touched the same files."""
