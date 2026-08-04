"""Bug entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.memory.entities.memory import Memory
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass(kw_only=True)
class Bug(Memory):
    """Records a bug with problem, root cause, and solution."""

    id: BugId
    problem: str
    root_cause: str
    solution: str
    affected_files: list[str] = field(default_factory=list)
    severity: str = "medium"
    resolved: bool = False
    resolved_at: datetime | None = None

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
        summary: str = "",
        body: str = "",
        source: str = "user",
        author: str | None = None,
    ) -> Bug:
        return cls(
            id=BugId(),
            project_id=project_id,
            memory_type="bug",
            title=title,
            summary=summary,
            body=body,
            source=source,
            author=author,
            problem=problem,
            root_cause=root_cause,
            solution=solution,
            affected_files=affected_files or [],
            severity=severity,
            resolved=True,
            resolved_at=datetime.now(UTC),
        )
