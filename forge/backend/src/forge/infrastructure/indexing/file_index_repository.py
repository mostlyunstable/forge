"""FileIndexRepository — implements IFileIndexRepository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.indexing.entities.file_index import FileIndex
from forge.domain.indexing.repository_contracts.file_index_repository import IFileIndexRepository
from forge.infrastructure.database.models.file_index_model import FileIndexModel


class FileIndexRepository(IFileIndexRepository):
    """SQLAlchemy implementation of IFileIndexRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, file_index: FileIndex) -> FileIndex:
        model = self._to_model(file_index)
        await self._session.merge(model)
        await self._session.flush()
        return self._to_domain(model)

    async def save_many(self, file_indices: list[FileIndex]) -> int:
        for fi in file_indices:
            existing = await self.get_by_project_and_path(fi.project_id, fi.file_path)
            if existing:
                fi.id = existing.id
            await self._session.merge(self._to_model(fi))
        await self._session.flush()
        return len(file_indices)

    async def get_by_project_and_path(
        self, project_id: UUID, file_path: str
    ) -> FileIndex | None:
        result = await self._session.execute(
            select(FileIndexModel).where(
                FileIndexModel.project_id == str(project_id),
                FileIndexModel.file_path == file_path,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(self, project_id: UUID) -> list[FileIndex]:
        result = await self._session.execute(
            select(FileIndexModel).where(
                FileIndexModel.project_id == str(project_id)
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_stale_files(
        self, project_id: UUID, current_hashes: dict[str, str]
    ) -> list[FileIndex]:
        result = await self._session.execute(
            select(FileIndexModel).where(
                FileIndexModel.project_id == str(project_id)
            )
        )
        all_files = [self._to_domain(m) for m in result.scalars().all()]
        return [
            fi for fi in all_files
            if fi.file_path in current_hashes
            and fi.needs_reindex(current_hashes[fi.file_path])
        ]

    async def delete_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            delete(FileIndexModel).where(
                FileIndexModel.project_id == str(project_id)
            )
        )
        await self._session.flush()
        return result.rowcount

    async def count_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                FileIndexModel.project_id == str(project_id)
            )
        )
        return result.scalar_one()

    def _to_domain(self, model: FileIndexModel) -> FileIndex:
        return FileIndex(
            id=UUID(model.id),
            project_id=UUID(model.project_id),
            file_path=model.file_path,
            content_hash=model.content_hash,
            language=model.language or "",
            last_indexed_commit=model.last_indexed_commit or "",
            parsed_at=model.parsed_at,
            index_job_id=UUID(model.index_job_id) if model.index_job_id else None,
        )

    def _to_model(self, entity: FileIndex) -> FileIndexModel:
        return FileIndexModel(
            id=str(entity.id),
            project_id=str(entity.project_id),
            file_path=entity.file_path,
            content_hash=entity.content_hash,
            language=entity.language,
            last_indexed_commit=entity.last_indexed_commit,
            parsed_at=entity.parsed_at,
            index_job_id=str(entity.index_job_id) if entity.index_job_id else None,
        )
