"""CreateProjectUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.projects.entities.project import Project
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.projects.exceptions import ProjectAlreadyExistsError
from forge.domain.projects.events import ProjectCreated
from forge.domain.shared.events import IEventBus


@dataclass
class CreateProjectRequest:
    """Input DTO for creating a project."""

    name: str
    description: str
    stack: list[str]
    goals: list[str] | None = None
    repository_url: str | None = None


@dataclass
class CreateProjectResponse:
    """Output DTO after creating a project."""

    id: str
    name: str
    description: str
    stack: list[str]
    goals: list[str]
    status: str
    created_at: str
    updated_at: str


class CreateProjectUseCase:
    """Creates a new project. Single responsibility: project creation."""

    def __init__(
        self,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, request: CreateProjectRequest) -> CreateProjectResponse:
        existing = await self._project_repo.get_by_name(request.name)
        if existing:
            raise ProjectAlreadyExistsError(request.name)

        project = Project.create(
            name=request.name,
            description=request.description,
            stack=TechStack.from_list(request.stack),
            goals=request.goals,
            repository_url=request.repository_url,
        )

        saved = await self._project_repo.save(project)

        if self._event_bus:
            await self._event_bus.publish(
                ProjectCreated(
                    project_id=str(saved.id),
                    project_name=saved.name,
                )
            )

        return CreateProjectResponse(
            id=str(saved.id),
            name=saved.name,
            description=saved.description,
            stack=list(saved.stack),
            goals=saved.goals,
            status=saved.status,
            created_at=str(saved.created_at),
            updated_at=str(saved.updated_at),
        )
