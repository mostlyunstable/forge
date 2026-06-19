"""Bug entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class Bug:
    """Records a bug with problem, root cause, and solution."""

    id: BugId
    project_id: ProjectId
    title: str
    problem: str
    root_cause: str
    solution: str
    affected_files: list[str] = field(default_factory=list)
    severity: str = "medium"
    resolved: bool = False
    resolved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_unresolved(self) -> None:
        self.resolved = False
        self.resolved_at = None

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        problem: str,
        root_cause: str,
        solution: str,
        affected_files: list[str] | None = None,
        severity: str = "medium",
    ) -> Bug:
        return cls(
            id=BugId(),
            project_id=project_id,
            title=title,
            problem=problem,
            root_cause=root_cause,
            solution=solution,
            affected_files=affected_files or [],
            severity=severity,
            resolved=True,
            resolved_at=datetime.now(timezone.utc),
        )
