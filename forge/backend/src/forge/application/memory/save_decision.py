"""SaveDecisionUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.events import DecisionRecorded
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.shared.events import IEventBus


@dataclass
class SaveDecisionRequest:
    """Input DTO for saving an architectural decision."""

    project_id: str
    title: str
    decision: str
    reason: str
    alternatives: list[str] | None = None


@dataclass
class SaveDecisionResponse:
    """Output DTO after saving a decision."""

    id: str
    project_id: str
    title: str
    decision: str
    reason: str
    alternatives: list[str]
    status: str
    created_at: str


class SaveDecisionUseCase:
    """Saves an architectural decision for a project."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._decision_repo = decision_repo
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, request: SaveDecisionRequest) -> SaveDecisionResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        decision = ArchitectureDecision.create(
            project_id=project.id,
            title=request.title,
            decision=request.decision,
            reason=request.reason,
            alternatives=request.alternatives,
        )

        saved = await self._decision_repo.save(decision)

        if self._event_bus:
            await self._event_bus.publish(
                DecisionRecorded(
                    decision_id=str(saved.id),
                    project_id=str(saved.project_id),
                    title=saved.title,
                )
            )

        return SaveDecisionResponse(
            id=str(saved.id),
            project_id=str(saved.project_id),
            title=saved.title,
            decision=saved.decision,
            reason=saved.reason,
            alternatives=saved.alternatives,
            status=saved.status,
            created_at=saved.created_at.isoformat(),
        )
