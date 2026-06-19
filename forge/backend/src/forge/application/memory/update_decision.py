"""UpdateDecisionUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.memory.exceptions import DecisionNotFoundError
from forge.domain.shared.events import IEventBus


@dataclass
class UpdateDecisionRequest:
    """Input DTO for updating a decision."""

    decision_id: str
    title: str | None = None
    decision: str | None = None
    reason: str | None = None
    alternatives: list[str] | None = None
    status: str | None = None


@dataclass
class UpdateDecisionResponse:
    """Output DTO after updating a decision."""

    id: str
    project_id: str
    title: str
    decision: str
    reason: str
    alternatives: list[str]
    status: str
    created_at: str


class UpdateDecisionUseCase:
    """Updates an existing decision."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._decision_repo = decision_repo
        self._event_bus = event_bus

    async def execute(self, request: UpdateDecisionRequest) -> UpdateDecisionResponse:
        decision = await self._decision_repo.get_by_id(DecisionId.from_string(request.decision_id))
        if not decision:
            raise DecisionNotFoundError(request.decision_id)

        if request.title is not None:
            decision.title = request.title
        if request.decision is not None:
            decision.decision = request.decision
        if request.reason is not None:
            decision.update_reason(request.reason)
        if request.alternatives is not None:
            decision.alternatives = request.alternatives
        if request.status is not None:
            decision.status = request.status

        saved = await self._decision_repo.save(decision)

        return UpdateDecisionResponse(
            id=str(saved.id),
            project_id=str(saved.project_id),
            title=saved.title,
            decision=saved.decision,
            reason=saved.reason,
            alternatives=saved.alternatives,
            status=saved.status,
            created_at=saved.created_at.isoformat(),
        )
