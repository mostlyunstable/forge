"""DeleteProjectUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.events import ProjectDeleted
from forge.domain.shared.events import IEventBus


@dataclass
class DeleteProjectResponse:
    """Output DTO after deleting a project."""

    deleted: bool
    project_id: str


class DeleteProjectUseCase:
    """Deletes a project and its associated data."""

    def __init__(
        self,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, project_id: str) -> DeleteProjectResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(project_id))
        if not project:
            raise ProjectNotFoundError(project_id)

        deleted = await self._project_repo.delete(ProjectId.from_string(project_id))

        if self._event_bus and deleted:
            await self._event_bus.publish(
                ProjectDeleted(project_id=project_id)
            )

        return DeleteProjectResponse(deleted=deleted, project_id=project_id)
