"""Code domain events."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class CodeEntriesBatchIndexed(DomainEvent):
    """Published when a batch of code entries are indexed."""

    project_id: str = ""
    entry_count: int = 0
    repo_path: str = ""

    @property
    def event_type(self) -> str:
        return "code.batch_indexed"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["entry_count"] = self.entry_count
        base["repo_path"] = self.repo_path
        return base


@dataclass(frozen=True)
class CodeIndexCleared(DomainEvent):
    """Published when a project's code index is cleared."""

    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "code.index_cleared"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        return base
