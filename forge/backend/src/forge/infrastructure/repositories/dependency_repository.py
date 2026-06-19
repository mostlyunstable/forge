"""DependencyRepository - implements IDependencyRepository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.code.entities.code_dependency import CodeDependency
from forge.domain.code.repository_contracts.dependency_repository import IDependencyRepository
from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.base import Base


class DependencyModel(Base):
    __tablename__ = "code_dependencies"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    source_entry_id = Column(String(36), nullable=False)
    target_entry_id = Column(String(36), nullable=True)
    dependency_type = Column(String(50), nullable=False)
    source_file = Column(String(500), nullable=False)
    target_file = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DependencyRepository(IDependencyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_batch(self, dependencies: list[CodeDependency]) -> None:
        for dep in dependencies:
            model = DependencyModel(
                id=str(dep.id),
                project_id=str(dep.project_id.value),
                source_entry_id=str(dep.source_entry_id),
                target_entry_id=str(dep.target_entry_id) if dep.target_entry_id else None,
                dependency_type=dep.dependency_type.value,
                source_file=dep.source_file,
                target_file=dep.target_file,
                line_number=dep.line_number,
                metadata_=dep.metadata,
                created_at=dep.created_at,
            )
            self._session.add(model)
        await self._session.flush()

    async def find_by_source(self, project_id: ProjectId, file_path: str) -> list[CodeDependency]:
        result = await self._session.execute(
            __import__("sqlalchemy").select(DependencyModel).where(
                DependencyModel.project_id == str(project_id.value),
                DependencyModel.source_file == file_path,
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def find_by_target(self, project_id: ProjectId, file_path: str) -> list[CodeDependency]:
        result = await self._session.execute(
            __import__("sqlalchemy").select(DependencyModel).where(
                DependencyModel.project_id == str(project_id.value),
                DependencyModel.target_file == file_path,
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def find_all(self, project_id: ProjectId) -> list[CodeDependency]:
        result = await self._session.execute(
            __import__("sqlalchemy").select(DependencyModel).where(
                DependencyModel.project_id == str(project_id.value)
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete_by_project(self, project_id: ProjectId) -> None:
        from sqlalchemy import delete
        await self._session.execute(
            delete(DependencyModel).where(
                DependencyModel.project_id == str(project_id.value)
            )
        )

    def _to_domain(self, model: DependencyModel) -> CodeDependency:
        from uuid import UUID as UUIDType
        return CodeDependency(
            id=UUIDType(model.id),
            project_id=ProjectId(UUIDType(model.project_id)),
            source_entry_id=UUIDType(model.source_entry_id),
            target_entry_id=UUIDType(model.target_entry_id) if model.target_entry_id else None,
            dependency_type=DependencyType(model.dependency_type),
            source_file=model.source_file,
            target_file=model.target_file,
            line_number=model.line_number,
            metadata=model.metadata_ or {},
            created_at=model.created_at,
        )
