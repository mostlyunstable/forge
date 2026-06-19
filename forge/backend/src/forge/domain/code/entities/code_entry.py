"""CodeEntry entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.code.value_objects.code_location import FilePath, LineRange
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CodeEntry:
    """A code entry extracted from a repository by Tree-sitter."""

    id: uuid.UUID
    project_id: ProjectId
    file_path: FilePath
    entry_type: EntryType
    name: str
    content: str
    language: str
    lines: LineRange
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def display_name(self) -> str:
        return f"{self.entry_type.value}: {self.name}"

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        file_path: str,
        entry_type: EntryType,
        name: str,
        content: str,
        language: str,
        start_line: int,
        end_line: int,
        metadata: dict | None = None,
    ) -> CodeEntry:
        return cls(
            id=uuid.uuid4(),
            project_id=project_id,
            file_path=FilePath(file_path),
            entry_type=entry_type,
            name=name,
            content=content,
            language=language,
            lines=LineRange(start=start_line, end=end_line),
            metadata=metadata or {},
        )
