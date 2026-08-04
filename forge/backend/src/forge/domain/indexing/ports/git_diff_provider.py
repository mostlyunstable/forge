"""IGitDiffProvider — port for git diff operations."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IGitDiffProvider(ABC):
    """Interface for git diff operations."""

    @abstractmethod
    def get_changed_files(self, repo_path: str, from_ref: str, to_ref: str = "HEAD") -> list[dict]:
        """Get files changed between two refs.

        Returns list of dicts with:
        - file_path: str
        - change_type: str (added, modified, deleted, renamed)
        - additions: int
        - deletions: int
        """

    @abstractmethod
    def get_commit_files(self, repo_path: str, commit_sha: str) -> list[dict]:
        """Get files changed in a specific commit."""

    @abstractmethod
    def get_latest_commit(self, repo_path: str) -> str | None:
        """Get the latest commit SHA."""
