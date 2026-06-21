"""IGitCommitParser — port for parsing git commits."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParsedCommit:
    """A parsed git commit with extracted metadata."""

    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: str
    parent_shas: list[str]
    files_changed: list[str]


class IGitCommitParser(ABC):
    """Interface for parsing git commits."""

    @abstractmethod
    def get_commit_history(
        self, repo_path: str, since: str | None = None, limit: int = 1000
    ) -> list[ParsedCommit]:
        """Get commit history from a git repository."""

    @abstractmethod
    def extract_from_message(self, commit: ParsedCommit) -> list[dict]:
        """Extract knowledge from a commit message."""
