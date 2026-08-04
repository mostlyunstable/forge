"""GetProjectUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository


@dataclass
class GetProjectResponse:
    """Output DTO for retrieving a project."""

    id: str
    name: str
    description: str
    stack: list[str]
    goals: list[str]
    status: str
    repository_url: str | None
    created_at: str
    updated_at: str


class GetProjectUseCase:
    """Retrieves a single project by ID."""

    def __init__(self, project_repo: IProjectRepository) -> None:
        self._project_repo = project_repo

    async def execute(self, project_id: str) -> GetProjectResponse:
        from forge.domain.projects.value_objects.project_id import ProjectId

        project = await self._project_repo.get_by_id(ProjectId.from_string(project_id))
        if not project:
            raise ProjectNotFoundError(project_id)

        return GetProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            stack=list(project.stack),
            goals=project.goals,
            status=project.status,
            repository_url=project.repository_url,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )
