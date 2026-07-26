"""EngineeringEvent entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from dataclasses import FrozenInstanceError

from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.entities.memory import Memory

@dataclass(kw_only=True)
class EngineeringEvent(Memory):
    """An immutable record of an event that occurred in the engineering process."""

    event_type: str
    event_data: dict[str, Any] = field(default_factory=dict)
    _initialized: bool = field(default=False, init=False, repr=False, hash=False, compare=False)

    def __post_init__(self):
        self._initialized = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_initialized", False) and name != "_initialized":
            raise FrozenInstanceError(f"cannot assign to field {name!r}, EngineeringEvent is immutable")
        super().__setattr__(name, value)

    def update_content(self, title: str, summary: str, body: str) -> None:
        raise FrozenInstanceError("EngineeringEvent is immutable and cannot be updated.")

    def archive(self) -> None:
        raise FrozenInstanceError("EngineeringEvent is immutable and cannot be archived.")

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        event_type: str,
        summary: str = "",
        body: str = "",
        source: str = "system",
        author: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> EngineeringEvent:
        return cls(
            id=MemoryId(),
            project_id=project_id,
            memory_type="event",
            title=title,
            summary=summary,
            body=body,
            source=source,
            author=author,
            event_type=event_type,
            event_data=event_data or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
