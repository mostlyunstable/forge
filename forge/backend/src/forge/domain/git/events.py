"""Git domain events."""
from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class CommitClassified(DomainEvent):
    """Published when a commit is analyzed and classified."""

    project_id: str = ""
    sha: str = ""
    classification: str = ""
    summary: str = ""

    @property
    def event_type(self) -> str:
        return "commit.classified"

    def to_dict(self):
        base = super().to_dict()
        base["project_id"] = self.project_id
        base["sha"] = self.sha
        base["classification"] = self.classification
        base["summary"] = self.summary
        return base
