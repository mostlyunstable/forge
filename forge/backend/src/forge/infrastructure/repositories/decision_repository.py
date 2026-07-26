"""DecisionRepository - implements IDecisionRepository."""
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure._utils import escape_like_pattern
from forge.infrastructure.database.models.memory_model import DecisionModel


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
            # Update base Memory properties
            model.title = decision.title
            model.summary = decision.summary
            model.body = decision.body
            model.source = decision.source
            model.author = decision.author
            model.updated_at = decision.updated_at
            model.metadata_json = decision.metadata
            model.embedding_reference = decision.embedding_reference
            model.version_number = decision.version_number
            model.previous_version_id = str(decision.previous_version_id.value) if decision.previous_version_id else None
            model.superseded_by_id = str(decision.superseded_by_id.value) if decision.superseded_by_id else None
            model.archived_at = decision.archived_at
            # Update Decision properties
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

    def _to_domain(self, model: DecisionModel) -> ArchitectureDecision:
        from forge.domain.memory.value_objects.memory_id import MemoryId
        base_kwargs = {
            "id": DecisionId(uuid.UUID(model.id)),
            "project_id": ProjectId(uuid.UUID(model.project_id)),
            "memory_type": model.memory_type,
            "title": model.title,
            "summary": model.summary,
            "body": model.body,
            "source": model.source,
            "author": model.author,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "metadata": model.metadata_json,
            "embedding_reference": model.embedding_reference,
            "version_number": model.version_number,
            "previous_version_id": MemoryId(uuid.UUID(model.previous_version_id)) if model.previous_version_id else None,
            "superseded_by_id": MemoryId(uuid.UUID(model.superseded_by_id)) if model.superseded_by_id else None,
            "archived_at": model.archived_at,
        }
        dec = ArchitectureDecision.__new__(ArchitectureDecision)
        dec.__dict__.update(base_kwargs)
        dec.decision = model.decision
        dec.reason = model.reason
        dec.alternatives = model.alternatives or []
        dec.status = model.status
        return dec

    def _to_model(self, entity: ArchitectureDecision) -> DecisionModel:
        return DecisionModel(
            id=str(entity.id.value),
            project_id=str(entity.project_id.value),
            memory_type=entity.memory_type,
            title=entity.title,
            summary=entity.summary,
            body=entity.body,
            source=entity.source,
            author=entity.author,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            metadata_json=entity.metadata,
            embedding_reference=entity.embedding_reference,
            version_number=entity.version_number,
            previous_version_id=str(entity.previous_version_id.value) if entity.previous_version_id else None,
            superseded_by_id=str(entity.superseded_by_id.value) if entity.superseded_by_id else None,
            archived_at=entity.archived_at,
            decision=entity.decision,
            reason=entity.reason,
            alternatives=entity.alternatives,
            status=entity.status,
        )

    async def search_by_title(self, query: str) -> list[ArchitectureDecision]:
        safe_pattern = f"%{escape_like_pattern(query)}%"
        result = await self._session.execute(
            select(DecisionModel).where(DecisionModel.title.ilike(safe_pattern))
        )
        return [self._to_domain(m) for m in result.scalars().all()]
