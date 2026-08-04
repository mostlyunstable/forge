"""IMemoryRepository - contract for base memory persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod

from forge.domain.memory.entities.memory import Memory
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId


class IMemoryRepository(ABC):
    """Interface for base memory persistence."""

    @abstractmethod
    async def get_by_id(self, memory_id: MemoryId) -> Memory | None:
        """Retrieve a memory by its ID."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> list[Memory]:
        """Retrieve all memories for a project, newest first."""

    @abstractmethod
    async def save(self, memory: Memory) -> Memory:
        """Persist a new or updated memory."""

    @abstractmethod
    async def delete(self, memory_id: MemoryId) -> bool:
        """Delete a memory by ID."""
