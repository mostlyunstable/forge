"""ListBugsUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.exceptions import ProjectNotFoundError


@dataclass
class BugSummary:
    """Summary of a bug for list view."""

    id: str
    title: str
    severity: str
    resolved: bool
    created_at: str


@dataclass
class ListBugsResponse:
    """Output DTO for listing bugs."""

    bugs: list[BugSummary]
    total: int
    project_id: str


class ListBugsUseCase:
    """Lists all bugs for a project."""

    def __init__(
        self,
        bug_repo: IBugRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._bug_repo = bug_repo
        self._project_repo = project_repo

    async def execute(self, project_id: str, skip: int = 0, limit: int = 100) -> ListBugsResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(project_id))
        if not project:
            raise ProjectNotFoundError(project_id)

        bugs = await self._bug_repo.get_by_project(ProjectId.from_string(project_id))
        total = len(bugs)
        paginated = bugs[skip:skip + limit]

        return ListBugsResponse(
            bugs=[
                BugSummary(
                    id=str(b.id),
                    title=b.title,
                    severity=b.severity,
                    resolved=b.resolved,
                    created_at=b.created_at.isoformat(),
                )
                for b in paginated
            ],
            total=total,
            project_id=project_id,
        )
