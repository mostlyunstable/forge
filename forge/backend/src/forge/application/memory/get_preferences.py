"""GetPreferencesUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.preference_repository import IPreferenceRepository


@dataclass
class PreferenceSummary:
    """A developer preference summary."""

    key: str
    value: str
    confidence: float
    evidence_count: int


@dataclass
class GetPreferencesResponse:
    """Output DTO for listing preferences."""

    preferences: list[PreferenceSummary]
    total: int


class GetPreferencesUseCase:
    """Retrieves all developer preferences."""

    def __init__(self, preference_repo: IPreferenceRepository) -> None:
        self._preference_repo = preference_repo

    async def execute(self) -> GetPreferencesResponse:
        preferences = await self._preference_repo.get_all()

        summaries = [
            PreferenceSummary(
                key=str(p.key),
                value=p.value,
                confidence=p.confidence,
                evidence_count=p.evidence_count,
            )
            for p in preferences
        ]

        return GetPreferencesResponse(preferences=summaries, total=len(summaries))
