"""IGraphAdapter - Repository contract for the knowledge graph."""
from __future__ import annotations

import abc
from typing import Any

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType


class IGraphAdapter(abc.ABC):
    """Abstract interface for knowledge graph operations."""

    @abc.abstractmethod
    async def add_relationships(self, project_id: ProjectId, relationships: list[Relationship]) -> None:
        """Add a batch of relationships to the knowledge graph."""
        pass

    @abc.abstractmethod
    async def delete_relationships_for_source(self, project_id: ProjectId, source_id: str) -> None:
        """Delete all relationships where the given entity is the source."""
        pass

    @abc.abstractmethod
    async def get_relationships(
        self, 
        project_id: ProjectId, 
        source_id: str | None = None, 
        target_id: str | None = None,
        relationship_type: RelationshipType | None = None
    ) -> list[Relationship]:
        """Get relationships matching the criteria."""
        pass

    @abc.abstractmethod
    async def traverse(
        self,
        project_id: ProjectId,
        start_id: str,
        max_depth: int = 1,
        relationship_types: list[RelationshipType] | None = None,
        direction: str = "outbound"
    ) -> list[dict[str, Any]]:
        """
        Perform a multi-hop traversal from the start_id.
        direction can be "outbound", "inbound", or "both".
        Returns a list of dictionaries containing path information or the visited edges.
        """
        pass
