"""Relationship entity for Knowledge Graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from forge.domain.projects.value_objects.project_id import ProjectId


class RelationshipType(StrEnum):
    """Types of relationships in the knowledge graph."""

    AFFECTS = "affects"
    REFERENCES = "references"
    IMPLEMENTS = "implements"
    FIXES = "fixes"
    SUPERSEDES = "supersedes"
    CAUSED_BY = "caused_by"
    DEPENDS_ON = "depends_on"
    INTRODUCED = "introduced"
    REMOVED = "removed"
    DOCUMENTS = "documents"
    DISCUSSES = "discusses"
    RELATED_TO = "related_to"


@dataclass
class Relationship:
    """A knowledge graph relationship between two entities."""

    id: uuid.UUID
    project_id: ProjectId
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

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
