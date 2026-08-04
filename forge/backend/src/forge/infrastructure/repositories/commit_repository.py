# mypy: disable-error-code="assignment, arg-type"
"""CommitRepository - implements ICommitRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.git.entities.commit import Commit
from forge.domain.git.repository_contracts.commit_repository import ICommitRepository
from forge.domain.git.value_objects.commit_classification import CommitClassification
from forge.domain.git.value_objects.commit_sha import CommitSha
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.commit_model import CommitModel


class CommitRepository(ICommitRepository):
    """SQLAlchemy implementation of ICommitRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sha(self, project_id: ProjectId, sha: CommitSha) -> Commit | None:
        result = await self._session.execute(
            select(CommitModel).where(
                CommitModel.project_id == str(project_id.value),
                CommitModel.sha == sha.value,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(self, project_id: ProjectId) -> list[Commit]:
        result = await self._session.execute(
            select(CommitModel)
            .where(CommitModel.project_id == str(project_id.value))
            .order_by(CommitModel.timestamp.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_classification(
        self, project_id: ProjectId, classification: CommitClassification
    ) -> list[Commit]:
        result = await self._session.execute(
            select(CommitModel)
            .where(
                CommitModel.project_id == str(project_id.value),
                CommitModel.classification == classification.value,
            )
            .order_by(CommitModel.timestamp.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_recent(self, project_id: ProjectId, limit: int = 10) -> list[Commit]:
        result = await self._session.execute(
            select(CommitModel)
            .where(CommitModel.project_id == str(project_id.value))
            .order_by(CommitModel.timestamp.desc())
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, commit: Commit) -> Commit:
        result = await self._session.execute(
            select(CommitModel).where(
                CommitModel.project_id == str(commit.project_id.value),
                CommitModel.sha == commit.sha.value,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            model.message = commit.message
            model.author = commit.author
            model.files_changed = commit.files_changed
            model.classification = commit.classification.value
            model.summary = commit.summary
            await self._session.flush()
            return self._to_domain(model)
        new_model = self._to_model(commit)
        self._session.add(new_model)
        await self._session.flush()
        return self._to_domain(new_model)

    async def save_many(self, commits: list[Commit]) -> list[Commit]:
        models = [self._to_model(c) for c in commits]
        self._session.add_all(models)
        await self._session.flush()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: CommitModel) -> Commit:
        from uuid import UUID

        return Commit(
            project_id=ProjectId(UUID(model.project_id)),
            sha=CommitSha(model.sha),
            message=model.message,
            author=model.author or "",
            timestamp=model.timestamp,
            files_changed=model.files_changed or [],
            classification=CommitClassification(model.classification),
            summary=model.summary or "",
            created_at=model.created_at,
        )

    def _to_model(self, entity: Commit) -> CommitModel:
        return CommitModel(
            project_id=str(entity.project_id.value),
            sha=entity.sha.value,
            message=entity.message,
            author=entity.author,
            timestamp=entity.timestamp,
            files_changed=entity.files_changed,
            classification=entity.classification.value,
            summary=entity.summary,
            created_at=entity.created_at,
        )
