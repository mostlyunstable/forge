"""SaveBugUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.events import BugRecorded
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.shared.events import IEventBus


@dataclass
class SaveBugRequest:
    """Input DTO for saving a bug fix record."""

    project_id: str
    title: str
    problem: str
    root_cause: str
    solution: str
    affected_files: list[str] | None = None
    severity: str = "medium"


@dataclass
class SaveBugResponse:
    """Output DTO after saving a bug."""

    id: str
    project_id: str
    title: str
    problem: str
    root_cause: str
    solution: str
    affected_files: list[str]
    severity: str
    resolved: bool
    created_at: str


class SaveBugUseCase:
    """Saves a bug fix record for a project."""

    def __init__(
        self,
        bug_repo: IBugRepository,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._bug_repo = bug_repo
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, request: SaveBugRequest) -> SaveBugResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        bug = Bug.create(
            project_id=project.id,
            title=request.title,
            problem=request.problem,
            root_cause=request.root_cause,
            solution=request.solution,
            affected_files=request.affected_files,
            severity=request.severity,
        )

        saved = await self._bug_repo.save(bug)

        if self._event_bus:
            await self._event_bus.publish(
                BugRecorded(
                    bug_id=str(saved.id),
                    project_id=str(saved.project_id),
                    title=saved.title,
                )
            )

        return SaveBugResponse(
            id=str(saved.id),
            project_id=str(saved.project_id),
            title=saved.title,
            problem=saved.problem,
            root_cause=saved.root_cause,
            solution=saved.solution,
            affected_files=saved.affected_files,
            severity=saved.severity,
            resolved=saved.resolved,
            created_at=saved.created_at.isoformat(),
        )
