"""Generic Memory base entity."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass(kw_only=True)
class Memory(ABC):
    """
    Base entity for all persistent engineering knowledge.

    Fields:
    - id
    - project_id
    - memory_type
    - title
    - summary
    - body
    - source
    - author
    - created_at
    - updated_at
    - metadata
    - embedding_reference
    - version_number
    - previous_version_id
    - superseded_by_id
    - archived_at
    """

    id: MemoryId
    project_id: ProjectId
    memory_type: str
    title: str
    summary: str
    body: str
    source: str
    author: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding_reference: str | None = None
    version_number: int = 1
    previous_version_id: MemoryId | None = None
    superseded_by_id: MemoryId | None = None
    archived_at: datetime | None = None

    def archive(self) -> None:
        """Mark the memory as archived."""
        self.archived_at = datetime.now(UTC)
        self.updated_at = self.archived_at

    def update_content(self, title: str, summary: str, body: str) -> None:
        """Update core content (often handled via versioning)."""
        self.title = title
        self.summary = summary
        self.body = body
        self.updated_at = datetime.now(UTC)
