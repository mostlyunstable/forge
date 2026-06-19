"""BugRepository - implements IBugRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain._utils import escape_like_pattern
from forge.infrastructure.database.models.bug_model import BugModel


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
        existing = await self.get_by_id(bug.id)
        if existing:
            model = await self._session.get(BugModel, str(bug.id.value))
            if model:
                model.title = bug.title
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
        from uuid import UUID
        return Bug(
            id=BugId(UUID(model.id)),
            project_id=ProjectId(UUID(model.project_id)),
            title=model.title,
            problem=model.problem,
            root_cause=model.root_cause or "",
            solution=model.solution or "",
            affected_files=model.affected_files or [],
            severity=model.severity,
            resolved=model.resolved,
            resolved_at=model.resolved_at,
            created_at=model.created_at,
        )

    def _to_model(self, entity: Bug) -> BugModel:
        return BugModel(
            id=str(entity.id.value),
            project_id=str(entity.project_id.value),
            title=entity.title,
            problem=entity.problem,
            root_cause=entity.root_cause,
            solution=entity.solution,
            affected_files=entity.affected_files,
            severity=entity.severity,
            resolved=entity.resolved,
            resolved_at=entity.resolved_at,
            created_at=entity.created_at,
        )
