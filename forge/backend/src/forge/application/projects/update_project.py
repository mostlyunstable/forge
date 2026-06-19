"""UpdateProjectUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.projects.entities.project import Project
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.events import ProjectUpdated
from forge.domain.shared.events import IEventBus


@dataclass
class UpdateProjectRequest:
    """Input DTO for updating a project."""

    project_id: str
    description: str | None = None
    stack: list[str] | None = None
    goals: list[str] | None = None
    repository_url: str | None = None


@dataclass
class UpdateProjectResponse:
    """Output DTO after updating a project."""

    id: str
    name: str
    description: str
    stack: list[str]
    goals: list[str]
    status: str
    repository_url: str | None
    created_at: str
    updated_at: str


class UpdateProjectUseCase:
    """Updates an existing project's metadata."""

    def __init__(
        self,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, request: UpdateProjectRequest) -> UpdateProjectResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        changes: dict = {}

        if request.description is not None:
            project.update_description(request.description)
            changes["description"] = request.description

        if request.stack is not None:
            project.update_stack(TechStack.from_list(request.stack))
            changes["stack"] = request.stack

        if request.goals is not None:
            project.goals = request.goals
            project._touch()
            changes["goals"] = request.goals

        if request.repository_url is not None:
            project.repository_url = request.repository_url
            project._touch()
            changes["repository_url"] = request.repository_url

        saved = await self._project_repo.save(project)

        if self._event_bus and changes:
            await self._event_bus.publish(
                ProjectUpdated(
                    project_id=str(saved.id),
                    changes=changes,
                )
            )

        return UpdateProjectResponse(
            id=str(saved.id),
            name=saved.name,
            description=saved.description,
            stack=list(saved.stack),
            goals=saved.goals,
            status=saved.status,
            repository_url=saved.repository_url,
            created_at=str(saved.created_at),
            updated_at=str(saved.updated_at),
        )
