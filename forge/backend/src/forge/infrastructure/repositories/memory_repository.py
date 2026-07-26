"""SQLAlchemy implementation of IMemoryRepository."""
from typing import Optional

from sqlalchemy import select

from forge.domain.memory.entities.memory import Memory
from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.entities.feature import Feature
from forge.domain.memory.entities.note import EngineeringNote
from forge.domain.memory.entities.decision_log import DecisionLog
from forge.domain.memory.entities.event import EngineeringEvent
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.infrastructure.database.models.memory_model import (
    MemoryModel, BugModel, DecisionModel, FeatureModel,
    EngineeringNoteModel, DecisionLogModel, EngineeringEventModel
)
from forge.infrastructure.repositories.base_repository import BaseRepository

class MemoryRepository(BaseRepository, IMemoryRepository):
    async def get_by_id(self, memory_id: MemoryId) -> Optional[Memory]:
        model = await self._session.get(MemoryModel, str(memory_id.value))
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_project(self, project_id: ProjectId) -> list[Memory]:
        result = await self._session.execute(
            select(MemoryModel)
            .where(MemoryModel.project_id == str(project_id.value))
            .order_by(MemoryModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, memory: Memory) -> Memory:
        model = await self._session.get(MemoryModel, str(memory.id.value))
        if model:
            # Update existing
            updated_model = self._to_model(memory)
            # SQLAlchemy merge/update approach
            await self._session.merge(updated_model)
        else:
            # Insert new
            model = self._to_model(memory)
            self._session.add(model)
        
        await self._session.flush()
        return memory

    async def delete(self, memory_id: MemoryId) -> bool:
        model = await self._session.get(MemoryModel, str(memory_id.value))
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    def _to_domain(self, model: MemoryModel) -> Memory:
        base_kwargs = {
            "id": MemoryId(model.id),
            "project_id": ProjectId(model.project_id),
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
            "previous_version_id": MemoryId(model.previous_version_id) if model.previous_version_id else None,
            "superseded_by_id": MemoryId(model.superseded_by_id) if model.superseded_by_id else None,
            "archived_at": model.archived_at,
        }

        if isinstance(model, BugModel):
            bug = Bug.__new__(Bug)
            bug.__dict__.update(base_kwargs)
            bug.memory_type = "bug"
            bug.problem = model.problem
            bug.root_cause = model.root_cause
            bug.solution = model.solution
            bug.affected_files = model.affected_files
            bug.severity = model.severity
            bug.resolved = model.resolved
            bug.resolved_at = model.resolved_at
            return bug
        elif isinstance(model, DecisionModel):
            dec = ArchitectureDecision.__new__(ArchitectureDecision)
            dec.__dict__.update(base_kwargs)
            dec.memory_type = "decision"
            dec.decision = model.decision
            dec.reason = model.reason
            dec.alternatives = model.alternatives
            dec.status = model.status
            return dec
        elif isinstance(model, FeatureModel):
            feat = Feature.__new__(Feature)
            feat.__dict__.update(base_kwargs)
            feat.memory_type = "feature"
            feat.status = model.status
            feat.acceptance_criteria = model.acceptance_criteria
            return feat
        elif isinstance(model, EngineeringNoteModel):
            note = EngineeringNote.__new__(EngineeringNote)
            note.__dict__.update(base_kwargs)
            note.memory_type = "note"
            note.tags = model.tags
            return note
        elif isinstance(model, DecisionLogModel):
            log = DecisionLog.__new__(DecisionLog)
            log.__dict__.update(base_kwargs)
            log.memory_type = "decision_log"
            log.decisions_referenced = [MemoryId(mid) for mid in model.decisions_referenced]
            return log
        elif isinstance(model, EngineeringEventModel):
            evt = EngineeringEvent.__new__(EngineeringEvent)
            evt.__dict__.update(base_kwargs)
            evt.memory_type = "event"
            evt.event_type = model.event_type
            evt.event_data = model.event_data
            evt._initialized = True
            return evt
        else:
            raise ValueError(f"Unknown memory type: {type(model)}")

    def _to_model(self, entity: Memory) -> MemoryModel:
        base_kwargs = {
            "id": str(entity.id.value),
            "project_id": str(entity.project_id.value),
            "title": entity.title,
            "summary": entity.summary,
            "body": entity.body,
            "source": entity.source,
            "author": entity.author,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "metadata_json": entity.metadata,
            "embedding_reference": entity.embedding_reference,
            "version_number": entity.version_number,
            "previous_version_id": str(entity.previous_version_id.value) if entity.previous_version_id else None,
            "superseded_by_id": str(entity.superseded_by_id.value) if entity.superseded_by_id else None,
            "archived_at": entity.archived_at,
        }

        if isinstance(entity, Bug):
            return BugModel(
                **base_kwargs,
                problem=entity.problem,
                root_cause=entity.root_cause,
                solution=entity.solution,
                affected_files=entity.affected_files,
                severity=entity.severity,
                resolved=entity.resolved,
                resolved_at=entity.resolved_at
            )
        elif isinstance(entity, ArchitectureDecision):
            return DecisionModel(
                **base_kwargs,
                decision=entity.decision,
                reason=entity.reason,
                alternatives=entity.alternatives,
                status=entity.status
            )
        elif isinstance(entity, Feature):
            return FeatureModel(
                **base_kwargs,
                status=entity.status,
                acceptance_criteria=entity.acceptance_criteria
            )
        elif isinstance(entity, EngineeringNote):
            return EngineeringNoteModel(
                **base_kwargs,
                tags=entity.tags
            )
        elif isinstance(entity, DecisionLog):
            return DecisionLogModel(
                **base_kwargs,
                decisions_referenced=[str(d.value) for d in entity.decisions_referenced]
            )
        elif isinstance(entity, EngineeringEvent):
            return EngineeringEventModel(
                **base_kwargs,
                event_type=entity.event_type,
                event_data=entity.event_data
            )
        else:
            raise ValueError(f"Unknown memory entity type: {type(entity)}")
