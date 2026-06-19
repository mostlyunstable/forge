"""SavePreferenceUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.entities.preference import DeveloperPreference
from forge.domain.memory.repository_contracts.preference_repository import IPreferenceRepository
from forge.domain.memory.value_objects.preference_key import PreferenceKey
from forge.domain.memory.events import PreferenceRecorded, PreferenceStrengthened
from forge.domain.shared.events import IEventBus


@dataclass
class SavePreferenceRequest:
    """Input DTO for saving a developer preference."""

    key: str
    value: str
    confidence: float = 0.5


@dataclass
class SavePreferenceResponse:
    """Output DTO after saving a preference."""

    key: str
    value: str
    confidence: float
    evidence_count: int
    created_at: str
    updated_at: str


class SavePreferenceUseCase:
    """Saves or strengthens a developer preference."""

    def __init__(
        self,
        preference_repo: IPreferenceRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._preference_repo = preference_repo
        self._event_bus = event_bus

    async def execute(self, request: SavePreferenceRequest) -> SavePreferenceResponse:
        existing = await self._preference_repo.get_by_key(PreferenceKey(request.key))

        if existing:
            existing.strengthen(request.value)
            saved = await self._preference_repo.save(existing)
            if self._event_bus:
                await self._event_bus.publish(
                    PreferenceStrengthened(
                        preference_key=str(saved.key),
                        new_confidence=saved.confidence,
                        evidence_count=saved.evidence_count,
                    )
                )
        else:
            preference = DeveloperPreference.create(
                key=request.key,
                value=request.value,
                confidence=request.confidence,
            )
            saved = await self._preference_repo.save(preference)
            if self._event_bus:
                await self._event_bus.publish(
                    PreferenceRecorded(
                        preference_key=str(saved.key),
                        value=saved.value,
                    )
                )

        return SavePreferenceResponse(
            key=str(saved.key),
            value=saved.value,
            confidence=saved.confidence,
            evidence_count=saved.evidence_count,
            created_at=saved.created_at.isoformat(),
            updated_at=saved.updated_at.isoformat(),
        )
