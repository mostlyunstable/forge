"""DeletePreferenceUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.preference_repository import IPreferenceRepository
from forge.domain.memory.value_objects.preference_key import PreferenceKey
from forge.domain.memory.events import PreferenceDeleted
from forge.domain.shared.events import IEventBus


@dataclass
class DeletePreferenceResponse:
    """Output DTO after deleting a preference."""

    deleted: bool
    key: str


class DeletePreferenceUseCase:
    """Deletes a developer preference."""

    def __init__(
        self,
        preference_repo: IPreferenceRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._preference_repo = preference_repo
        self._event_bus = event_bus

    async def execute(self, key: str) -> DeletePreferenceResponse:
        deleted = await self._preference_repo.delete(PreferenceKey(key))

        if self._event_bus and deleted:
            await self._event_bus.publish(
                PreferenceDeleted(preference_key=key)
            )

        return DeletePreferenceResponse(deleted=deleted, key=key)
