# mypy: disable-error-code="assignment, arg-type"
"""PreferenceRepository - implements IPreferenceRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.memory.entities.preference import DeveloperPreference
from forge.domain.memory.repository_contracts.preference_repository import IPreferenceRepository
from forge.domain.memory.value_objects.preference_key import PreferenceKey
from forge.infrastructure.database.models.preference_model import PreferenceModel


class PreferenceRepository(IPreferenceRepository):
    """SQLAlchemy implementation of IPreferenceRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, key: PreferenceKey) -> DeveloperPreference | None:
        result = await self._session.execute(
            select(PreferenceModel).where(PreferenceModel.id == key.value)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[DeveloperPreference]:
        result = await self._session.execute(select(PreferenceModel).offset(skip).limit(limit))
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, preference: DeveloperPreference) -> DeveloperPreference:
        model = await self._session.get(PreferenceModel, str(preference.key))
        if model:
            model.value = preference.value
            model.confidence = preference.confidence
            model.evidence_count = preference.evidence_count
            model.updated_at = preference.updated_at
            await self._session.flush()
            return self._to_domain(model)
        model = self._to_model(preference)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, key: PreferenceKey) -> bool:
        result = await self._session.execute(
            select(PreferenceModel).where(PreferenceModel.id == key.value)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    def _to_domain(self, model: PreferenceModel) -> DeveloperPreference:
        return DeveloperPreference(
            key=PreferenceKey(model.id),
            value=model.value,
            confidence=model.confidence,
            evidence_count=model.evidence_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: DeveloperPreference) -> PreferenceModel:
        return PreferenceModel(
            id=str(entity.key),
            value=entity.value,
            confidence=entity.confidence,
            evidence_count=entity.evidence_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
