"""IDecisionRepository - contract for decision persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.projects.value_objects.project_id import ProjectId


class IDecisionRepository(ABC):
    """Interface for architecture decision persistence."""

    @abstractmethod
    async def get_by_id(self, decision_id: DecisionId) -> Optional[ArchitectureDecision]:
        """Retrieve a decision by its ID."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> list[ArchitectureDecision]:
        """Retrieve all decisions for a project, newest first."""

    @abstractmethod
    async def save(self, decision: ArchitectureDecision) -> ArchitectureDecision:
        """Persist a new or updated decision."""

    @abstractmethod
    async def delete(self, decision_id: DecisionId) -> bool:
        """Delete a decision by ID."""

    @abstractmethod
    async def search_by_title(self, query: str) -> list[ArchitectureDecision]:
        """Search decisions by title substring."""
