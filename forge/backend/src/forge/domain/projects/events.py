"""Project domain events."""
from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class ProjectCreated(DomainEvent):
    """Published when a new project is created."""

    project_id: str = ""
    project_name: str = ""

    @property
    def event_type(self) -> str:
        return "project.created"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["project_name"] = self.project_name
        return base


@dataclass(frozen=True)
class ProjectUpdated(DomainEvent):
    """Published when a project is updated."""

    project_id: str = ""
    changes: dict = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "project.updated"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["changes"] = self.changes
        return base


@dataclass(frozen=True)
class ProjectDeleted(DomainEvent):
    """Published when a project is deleted."""

    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "project.deleted"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        return base
