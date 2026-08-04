"""EngineeringNote entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.memory.entities.memory import Memory
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass(kw_only=True)
class EngineeringNote(Memory):
    """Records a general engineering note or observation."""

    tags: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        summary: str = "",
        body: str = "",
        source: str = "user",
        author: str | None = None,
        tags: list[str] | None = None,
    ) -> EngineeringNote:
        return cls(
            id=MemoryId(),
            project_id=project_id,
            memory_type="note",
            title=title,
            summary=summary,
            body=body,
            source=source,
            author=author,
            tags=tags or [],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
