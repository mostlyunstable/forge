"""IPreferenceRepository - contract for preference persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.memory.entities.preference import DeveloperPreference
from forge.domain.memory.value_objects.preference_key import PreferenceKey


class IPreferenceRepository(ABC):
    """Interface for developer preference persistence."""

    @abstractmethod
    async def get_by_key(self, key: PreferenceKey) -> Optional[DeveloperPreference]:
        """Retrieve a preference by its key."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[DeveloperPreference]:
        """Retrieve all preferences with pagination."""

    @abstractmethod
    async def save(self, preference: DeveloperPreference) -> DeveloperPreference:
        """Persist a new or updated preference."""

    @abstractmethod
    async def delete(self, key: PreferenceKey) -> bool:
        """Delete a preference by key."""
