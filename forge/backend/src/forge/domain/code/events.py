"""Code domain events."""
from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class DependencyGraphBuilt(DomainEvent):
    """Published when a dependency graph is built for a project."""

    project_id: str = ""
    node_count: int = 0
    edge_count: int = 0

    @property
    def event_type(self) -> str:
        return "dependency_graph.built"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["node_count"] = self.node_count
        base["edge_count"] = self.edge_count
        return base


@dataclass(frozen=True)
class CycleDetected(DomainEvent):
    """Published when a dependency cycle is detected."""

    project_id: str = ""
    cycle: list[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "dependency_graph.cycle_detected"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["cycle"] = self.cycle
        return base
