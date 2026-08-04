# mypy: disable-error-code="assignment, arg-type"
"""ExtractionCandidateRepository — implements IExtractionCandidateRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.indexing.entities.extraction_candidate import ExtractionCandidate
from forge.domain.indexing.repository_contracts.extraction_candidate_repository import (
    IExtractionCandidateRepository,
)
from forge.infrastructure.database.models.extraction_candidate_model import (
    ExtractionCandidateModel,
)
from forge.infrastructure.database.models.index_job_model import IndexJobModel


class ExtractionCandidateRepository(IExtractionCandidateRepository):
    """SQLAlchemy implementation of IExtractionCandidateRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, candidate: ExtractionCandidate) -> ExtractionCandidate:
        model = await self._session.get(ExtractionCandidateModel, str(candidate.id))
        if model:
            model.status = candidate.status
            model.reviewed_at = candidate.reviewed_at
            await self._session.flush()
            return self._to_domain(model)
        model = self._to_model(candidate)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def save_many(self, candidates: list[ExtractionCandidate]) -> int:
        saved = 0
        for c in candidates:
            existing = await self.get_by_dedup_key(c.dedup_key)
            if existing:
                c.status = "duplicate"
            else:
                self._session.add(self._to_model(c))
                saved += 1
        await self._session.flush()
        return saved

    async def get_by_id(self, candidate_id: UUID) -> ExtractionCandidate | None:
        result = await self._session.execute(
            select(ExtractionCandidateModel).where(ExtractionCandidateModel.id == str(candidate_id))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_dedup_key(self, dedup_key: str) -> ExtractionCandidate | None:
        result = await self._session.execute(
            select(ExtractionCandidateModel).where(ExtractionCandidateModel.dedup_key == dedup_key)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_job(self, job_id: UUID) -> list[ExtractionCandidate]:
        result = await self._session.execute(
            select(ExtractionCandidateModel).where(ExtractionCandidateModel.job_id == str(job_id))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_pending_review(
        self, project_id: UUID, limit: int = 50
    ) -> list[ExtractionCandidate]:
        result = await self._session.execute(
            select(ExtractionCandidateModel)
            .join(IndexJobModel, IndexJobModel.id == ExtractionCandidateModel.job_id)
            .where(
                IndexJobModel.project_id == str(project_id),
                ExtractionCandidateModel.status == "suggested",
            )
            .order_by(desc(ExtractionCandidateModel.confidence))
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_accepted(
        self, project_id: UUID, kind: str | None = None
    ) -> list[ExtractionCandidate]:
        stmt = (
            select(ExtractionCandidateModel)
            .join(IndexJobModel, IndexJobModel.id == ExtractionCandidateModel.job_id)
            .where(
                IndexJobModel.project_id == str(project_id),
                ExtractionCandidateModel.status == "accepted",
            )
        )
        if kind:
            stmt = stmt.where(ExtractionCandidateModel.kind == kind)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_project(self, project_id: UUID) -> dict[str, int]:
        result = await self._session.execute(
            select(
                ExtractionCandidateModel.kind,
                func.count(),
            )
            .join(IndexJobModel, IndexJobModel.id == ExtractionCandidateModel.job_id)
            .where(IndexJobModel.project_id == str(project_id))
            .group_by(ExtractionCandidateModel.kind)
        )
        return {row[0]: row[1] for row in result.all()}

    def _to_domain(self, model: ExtractionCandidateModel) -> ExtractionCandidate:
        return ExtractionCandidate(
            id=UUID(model.id),
            job_id=UUID(model.job_id),
            kind=model.kind,
            confidence=model.confidence,
            status=model.status,
            data=model.data or {},
            source_commit=model.source_commit or "",
            source_file=model.source_file or "",
            dedup_key=model.dedup_key or "",
            reviewed_at=model.reviewed_at,
            created_at=model.created_at,
        )

    def _to_model(self, entity: ExtractionCandidate) -> ExtractionCandidateModel:
        return ExtractionCandidateModel(
            id=str(entity.id),
            job_id=str(entity.job_id),
            kind=entity.kind,
            confidence=entity.confidence,
            status=entity.status,
            data=entity.data,
            source_commit=entity.source_commit,
            source_file=entity.source_file,
            dedup_key=entity.dedup_key,
            reviewed_at=entity.reviewed_at,
            created_at=entity.created_at,
        )
