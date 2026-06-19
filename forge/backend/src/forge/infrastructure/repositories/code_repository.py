"""CodeRepository - implements ICodeRepository."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.code.repository_contracts.code_repository import ICodeRepository
from forge.domain.code.value_objects.code_location import FilePath, LineRange
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure._utils import escape_like_pattern
from forge.infrastructure.database.models.code_entry_model import CodeEntryModel


class CodeRepository(ICodeRepository):
    """SQLAlchemy implementation of ICodeRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entry_id: UUID) -> Optional[CodeEntry]:
        result = await self._session.execute(
            select(CodeEntryModel).where(CodeEntryModel.id == str(entry_id))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(self, project_id: ProjectId) -> list[CodeEntry]:
        result = await self._session.execute(
            select(CodeEntryModel)
            .where(CodeEntryModel.project_id == str(project_id.value))
            .order_by(CodeEntryModel.file_path)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_file_path(self, project_id: ProjectId, file_path: str) -> list[CodeEntry]:
        result = await self._session.execute(
            select(CodeEntryModel)
            .where(
                CodeEntryModel.project_id == str(project_id.value),
                CodeEntryModel.file_path == file_path,
            )
            .order_by(CodeEntryModel.start_line)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_type(self, project_id: ProjectId, entry_type: EntryType) -> list[CodeEntry]:
        result = await self._session.execute(
            select(CodeEntryModel)
            .where(
                CodeEntryModel.project_id == str(project_id.value),
                CodeEntryModel.entry_type == entry_type.value,
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save_many(self, entries: list[CodeEntry]) -> list[CodeEntry]:
        models = [self._to_model(e) for e in entries]
        self._session.add_all(models)
        await self._session.flush()
        return [self._to_domain(m) for m in models]

    async def delete_by_project(self, project_id: ProjectId) -> bool:
        result = await self._session.execute(
            select(CodeEntryModel).where(CodeEntryModel.project_id == str(project_id.value))
        )
        for model in result.scalars().all():
            await self._session.delete(model)
        return True

    async def search_by_name(self, project_id: ProjectId, query: str) -> list[CodeEntry]:
        safe_pattern = f"%{escape_like_pattern(query)}%"
        result = await self._session.execute(
            select(CodeEntryModel)
            .where(
                CodeEntryModel.project_id == str(project_id.value),
                CodeEntryModel.name.ilike(safe_pattern),
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: CodeEntryModel) -> CodeEntry:
        from uuid import UUID
        return CodeEntry(
            id=UUID(model.id),
            project_id=ProjectId(UUID(model.project_id)),
            file_path=FilePath(model.file_path),
            entry_type=EntryType(model.entry_type),
            name=model.name,
            content=model.content or "",
            language=model.language or "",
            lines=LineRange(start=model.start_line, end=model.end_line),
            metadata=model.metadata or {},
            created_at=model.created_at,
        )

    def _to_model(self, entity: CodeEntry) -> CodeEntryModel:
        return CodeEntryModel(
            id=str(entity.id),
            project_id=str(entity.project_id.value),
            file_path=str(entity.file_path),
            entry_type=entity.entry_type.value,
            name=entity.name,
            content=entity.content,
            language=entity.language,
            start_line=entity.lines.start,
            end_line=entity.lines.end,
            metadata=entity.metadata,
            created_at=entity.created_at,
        )
