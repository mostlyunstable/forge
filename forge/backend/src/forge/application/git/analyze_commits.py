"""AnalyzeCommitsUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.git.repository_contracts.commit_repository import ICommitRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CommitSummary:
    """Lightweight commit representation."""

    sha: str
    message: str
    author: str
    classification: str
    files_changed: list[str]
    timestamp: str


@dataclass
class AnalyzeCommitsResponse:
    """Output DTO for commit analysis."""

    commits: list[CommitSummary]
    total: int
    by_classification: dict[str, int]


class AnalyzeCommitsUseCase:
    """Retrieves and summarizes commit history for a project."""

    def __init__(
        self,
        commit_repo: ICommitRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._commit_repo = commit_repo
        self._project_repo = project_repo

    async def execute(
        self,
        project_id: str,
        limit: int = 50,
    ) -> AnalyzeCommitsResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(project_id))
        if not project:
            raise ProjectNotFoundError(project_id)

        commits = await self._commit_repo.get_recent(project.id, limit=limit)

        by_classification: dict[str, int] = {}
        summaries = []
        for c in commits:
            class_key = c.classification.value
            by_classification[class_key] = by_classification.get(class_key, 0) + 1
            summaries.append(
                CommitSummary(
                    sha=c.sha.short,
                    message=c.message,
                    author=c.author,
                    classification=class_key,
                    files_changed=c.files_changed,
                    timestamp=c.timestamp.isoformat(),
                )
            )

        return AnalyzeCommitsResponse(
            commits=summaries,
            total=len(summaries),
            by_classification=by_classification,
        )
