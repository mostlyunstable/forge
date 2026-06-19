"""ProjectRepository - implements IProjectRepository."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.projects.entities.project import Project
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain._utils import escape_like_pattern
from forge.infrastructure.database.models.project_model import ProjectModel


class ProjectRepository(IProjectRepository):
    """SQLAlchemy implementation of IProjectRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == str(project_id.value))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_name(self, name: str) -> Optional[Project]:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel).offset(skip).limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, project: Project) -> Project:
        existing = await self.get_by_id(project.id)
        if existing:
            model = await self._session.get(ProjectModel, str(project.id.value))
            if model:
                model.name = project.name
                model.description = project.description
                model.stack = list(project.stack)
                model.goals = project.goals
                model.status = project.status
                model.repository_url = project.repository_url
                model.updated_at = project.updated_at
                await self._session.flush()
                return self._to_domain(model)
        model = self._to_model(project)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, project_id: ProjectId) -> bool:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == str(project_id.value))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    async def search_by_name(self, query: str) -> list[Project]:
        safe_pattern = f"%{escape_like_pattern(query)}%"
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.name.ilike(safe_pattern))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: ProjectModel) -> Project:
        return Project(
            id=ProjectId(UUID(model.id)),
            name=model.name,
            description=model.description or "",
            stack=TechStack.from_list(model.stack or []),
            goals=model.goals or [],
            status=model.status,
            repository_url=model.repository_url,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Project) -> ProjectModel:
        return ProjectModel(
            id=str(entity.id.value),
            name=entity.name,
            description=entity.description,
            stack=list(entity.stack),
            goals=entity.goals,
            status=entity.status,
            repository_url=entity.repository_url,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
