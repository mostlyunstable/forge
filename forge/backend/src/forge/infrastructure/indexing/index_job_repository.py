# mypy: disable-error-code="assignment, arg-type"
"""IndexJobRepository — implements IIndexJobRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.repository_contracts.index_job_repository import IIndexJobRepository
from forge.infrastructure.database.models.index_job_model import IndexJobModel


class IndexJobRepository(IIndexJobRepository):
    """SQLAlchemy implementation of IIndexJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: IndexJob) -> IndexJob:
        model = await self._session.get(IndexJobModel, str(job.id))
        if model:
            model.type = job.type.value
            model.status = job.status.value
            model.started_at = job.started_at
            model.completed_at = job.completed_at
            model.progress = job.progress
            model.result = job.result
            model.error_log = job.error_log
            model.checkpoint = job.checkpoint
            model.state_hash = job.state_hash
            await self._session.flush()
            return self._to_domain(model)
        model = self._to_model(job)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def get_by_id(self, job_id: UUID) -> IndexJob | None:
        result = await self._session.execute(
            select(IndexJobModel).where(IndexJobModel.id == str(job_id))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(
        self, project_id: UUID, limit: int = 20, skip: int = 0
    ) -> list[IndexJob]:
        result = await self._session.execute(
            select(IndexJobModel)
            .where(IndexJobModel.project_id == str(project_id))
            .order_by(desc(IndexJobModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_latest_completed(self, project_id: UUID) -> IndexJob | None:
        result = await self._session.execute(
            select(IndexJobModel)
            .where(
                IndexJobModel.project_id == str(project_id),
                IndexJobModel.status == "completed",
            )
            .order_by(desc(IndexJobModel.completed_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_running(self, project_id: UUID) -> IndexJob | None:
        result = await self._session.execute(
            select(IndexJobModel)
            .where(
                IndexJobModel.project_id == str(project_id),
                IndexJobModel.status == "running",
            )
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: IndexJobModel) -> IndexJob:
        from forge.domain.indexing.value_objects.index_type import IndexType
        from forge.domain.indexing.value_objects.job_status import JobStatus

        return IndexJob(
            id=UUID(model.id),
            project_id=UUID(model.project_id),
            type=IndexType(model.type),
            status=JobStatus(model.status),
            started_at=model.started_at,
            completed_at=model.completed_at,
            progress=model.progress or {},
            result=model.result or {},
            error_log=model.error_log or [],
            checkpoint=model.checkpoint or {},
            state_hash=model.state_hash or "",
            created_by=model.created_by or "api",
            created_at=model.created_at,
        )

    def _to_model(self, entity: IndexJob) -> IndexJobModel:
        return IndexJobModel(
            id=str(entity.id),
            project_id=str(entity.project_id),
            type=entity.type.value,
            status=entity.status.value,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            progress=entity.progress,
            result=entity.result,
            error_log=entity.error_log,
            checkpoint=entity.checkpoint,
            state_hash=entity.state_hash,
            created_by=entity.created_by,
            created_at=entity.created_at,
        )
