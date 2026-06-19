"""ListProjectsUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.projects.repository_contracts.project_repository import IProjectRepository


@dataclass
class ProjectSummary:
    """Lightweight project representation for lists."""

    id: str
    name: str
    description: str
    status: str
    stack: list[str]


@dataclass
class ListProjectsResponse:
    """Output DTO for listing projects."""

    projects: list[ProjectSummary]
    total: int


class ListProjectsUseCase:
    """Lists all projects with pagination."""

    def __init__(self, project_repo: IProjectRepository) -> None:
        self._project_repo = project_repo

    async def execute(self, skip: int = 0, limit: int = 100) -> ListProjectsResponse:
        projects = await self._project_repo.get_all(skip=skip, limit=limit)

        summaries = [
            ProjectSummary(
                id=str(p.id),
                name=p.name,
                description=p.description,
                status=p.status,
                stack=list(p.stack),
            )
            for p in projects
        ]

        return ListProjectsResponse(projects=summaries, total=len(summaries))
