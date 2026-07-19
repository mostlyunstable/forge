"""Relationship entity for Knowledge Graph."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from forge.domain.projects.value_objects.project_id import ProjectId


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph."""
    IMPLEMENTS = "implements"
    CALLS = "calls"
    IMPORTS = "imports"
    USES = "uses"
    COVERS = "covers"
    REFERENCES = "references"
    CONTAINS = "contains"


@dataclass
class Relationship:
    """A knowledge graph relationship between two entities."""
    id: uuid.UUID
    project_id: ProjectId
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        metadata: dict | None = None,
    ) -> Relationship:
        return cls(
            id=uuid.uuid4(),
            project_id=project_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {},
        )
