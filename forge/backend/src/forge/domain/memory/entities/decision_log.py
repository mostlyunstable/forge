"""DecisionLog entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.entities.memory import Memory

@dataclass(kw_only=True)
class DecisionLog(Memory):
    """Records a log or journal of decisions over time."""

    decisions_referenced: list[MemoryId] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        summary: str = "",
        body: str = "",
        source: str = "user",
        author: str | None = None,
        decisions_referenced: list[MemoryId] | None = None,
    ) -> DecisionLog:
        return cls(
            id=MemoryId(),
            project_id=project_id,
            memory_type="decision_log",
            title=title,
            summary=summary,
            body=body,
            source=source,
            author=author,
            decisions_referenced=decisions_referenced or [],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
