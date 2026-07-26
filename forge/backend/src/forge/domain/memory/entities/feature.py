"""Feature entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.entities.memory import Memory

@dataclass(kw_only=True)
class Feature(Memory):
    """Records a system feature or capability."""

    status: str = "planned"
    acceptance_criteria: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        summary: str = "",
        body: str = "",
        source: str = "user",
        author: str | None = None,
        status: str = "planned",
        acceptance_criteria: list[str] | None = None,
    ) -> Feature:
        return cls(
            id=MemoryId(),
            project_id=project_id,
            memory_type="feature",
            title=title,
            summary=summary,
            body=body,
            source=source,
            author=author,
            status=status,
            acceptance_criteria=acceptance_criteria or [],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
