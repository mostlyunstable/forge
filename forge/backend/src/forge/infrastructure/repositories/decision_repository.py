"""DecisionRepository - implements IDecisionRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain._utils import escape_like_pattern
from forge.infrastructure.database.models.decision_model import DecisionModel


class DecisionRepository(IDecisionRepository):
    """SQLAlchemy implementation of IDecisionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, decision_id: DecisionId) -> Optional[ArchitectureDecision]:
        result = await self._session.execute(
            select(DecisionModel).where(DecisionModel.id == str(decision_id.value))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(self, project_id: ProjectId) -> list[ArchitectureDecision]:
        result = await self._session.execute(
            select(DecisionModel)
            .where(DecisionModel.project_id == str(project_id.value))
            .order_by(DecisionModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, decision: ArchitectureDecision) -> ArchitectureDecision:
        model = await self._session.get(DecisionModel, str(decision.id.value))
        if model:
            model.title = decision.title
            model.decision = decision.decision
            model.reason = decision.reason
            model.alternatives = decision.alternatives
            model.status = decision.status
            await self._session.flush()
            return self._to_domain(model)
        model = self._to_model(decision)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, decision_id: DecisionId) -> bool:
        result = await self._session.execute(
            select(DecisionModel).where(DecisionModel.id == str(decision_id.value))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    async def search_by_title(self, query: str) -> list[ArchitectureDecision]:
        safe_pattern = f"%{escape_like_pattern(query)}%"
        result = await self._session.execute(
            select(DecisionModel).where(DecisionModel.title.ilike(safe_pattern))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: DecisionModel) -> ArchitectureDecision:
        from uuid import UUID
        return ArchitectureDecision(
            id=DecisionId(UUID(model.id)),
            project_id=ProjectId(UUID(model.project_id)),
            title=model.title,
            decision=model.decision,
            reason=model.reason or "",
            alternatives=model.alternatives or [],
            status=model.status,
            created_at=model.created_at,
        )

    def _to_model(self, entity: ArchitectureDecision) -> DecisionModel:
        return DecisionModel(
            id=str(entity.id.value),
            project_id=str(entity.project_id.value),
            title=entity.title,
            decision=entity.decision,
            reason=entity.reason,
            alternatives=entity.alternatives,
            status=entity.status,
            created_at=entity.created_at,
        )
