"""CodeDependency entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CodeDependency:
    """A dependency relationship between code entries."""

    id: uuid.UUID
    project_id: ProjectId
    source_entry_id: uuid.UUID
    target_entry_id: uuid.UUID | None
    dependency_type: DependencyType
    source_file: str
    target_file: str
    line_number: int
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        source_entry_id: uuid.UUID,
        target_entry_id: uuid.UUID | None,
        dependency_type: DependencyType,
        source_file: str,
        target_file: str,
        line_number: int,
        metadata: dict | None = None,
    ) -> CodeDependency:
        return cls(
            id=uuid.uuid4(),
            project_id=project_id,
            source_entry_id=source_entry_id,
            target_entry_id=target_entry_id,
            dependency_type=dependency_type,
            source_file=source_file,
            target_file=target_file,
            line_number=line_number,
            metadata=metadata or {},
        )
