"""BugRepository - implements IBugRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure._utils import escape_like_pattern
from forge.infrastructure.database.models.memory_model import BugModel


class BugRepository(IBugRepository):
    """SQLAlchemy implementation of IBugRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, bug_id: BugId) -> Optional[Bug]:
        result = await self._session.execute(
            select(BugModel).where(BugModel.id == str(bug_id.value))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(self, project_id: ProjectId) -> list[Bug]:
        result = await self._session.execute(
            select(BugModel)
            .where(BugModel.project_id == str(project_id.value))
            .order_by(BugModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_unresolved(self, project_id: ProjectId) -> list[Bug]:
        result = await self._session.execute(
            select(BugModel)
            .where(BugModel.project_id == str(project_id.value), BugModel.resolved.is_(False))
            .order_by(BugModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, bug: Bug) -> Bug:
        model = await self._session.get(BugModel, str(bug.id.value))
        if model:
            # Update base Memory properties
            model.title = bug.title
            model.summary = bug.summary
            model.body = bug.body
            model.source = bug.source
            model.author = bug.author
            model.updated_at = bug.updated_at
            model.metadata_json = bug.metadata
            model.embedding_reference = bug.embedding_reference
            model.version_number = bug.version_number
            model.previous_version_id = str(bug.previous_version_id.value) if bug.previous_version_id else None
            model.superseded_by_id = str(bug.superseded_by_id.value) if bug.superseded_by_id else None
            model.archived_at = bug.archived_at
            # Update Bug properties
            model.problem = bug.problem
            model.root_cause = bug.root_cause
            model.solution = bug.solution
            model.affected_files = bug.affected_files
            model.severity = bug.severity
            model.resolved = bug.resolved
            model.resolved_at = bug.resolved_at
            await self._session.flush()
            return self._to_domain(model)
        model = self._to_model(bug)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, bug_id: BugId) -> bool:
        result = await self._session.execute(
            select(BugModel).where(BugModel.id == str(bug_id.value))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    async def search_by_problem(self, query: str) -> list[Bug]:
        safe_pattern = f"%{escape_like_pattern(query)}%"
        result = await self._session.execute(
            select(BugModel).where(BugModel.problem.ilike(safe_pattern))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: BugModel) -> Bug:
        from forge.domain.memory.value_objects.memory_id import MemoryId
        base_kwargs = {
            "id": BugId(uuid.UUID(model.id)),
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
        bug = Bug.__new__(Bug)
        bug.__dict__.update(base_kwargs)
        bug.problem = model.problem
        bug.root_cause = model.root_cause or ""
        bug.solution = model.solution or ""
        bug.affected_files = model.affected_files or []
        bug.severity = model.severity
        bug.resolved = model.resolved
        bug.resolved_at = model.resolved_at
        return bug

    def _to_model(self, entity: Bug) -> BugModel:
        return BugModel(
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
            problem=entity.problem,
            root_cause=entity.root_cause,
            solution=entity.solution,
            affected_files=entity.affected_files,
            severity=entity.severity,
            resolved=entity.resolved,
            resolved_at=entity.resolved_at,
        )
