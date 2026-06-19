"""DeleteDecisionUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.memory.exceptions import DecisionNotFoundError
from forge.domain.memory.events import DecisionDeleted
from forge.domain.shared.events import IEventBus


@dataclass
class DeleteDecisionResponse:
    """Output DTO after deleting a decision."""

    deleted: bool
    decision_id: str


class DeleteDecisionUseCase:
    """Deletes a decision record."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._decision_repo = decision_repo
        self._event_bus = event_bus

    async def execute(self, decision_id: str) -> DeleteDecisionResponse:
        decision = await self._decision_repo.get_by_id(DecisionId.from_string(decision_id))
        if not decision:
            raise DecisionNotFoundError(decision_id)

        project_id = str(decision.project_id)
        deleted = await self._decision_repo.delete(DecisionId.from_string(decision_id))

        if self._event_bus and deleted:
            await self._event_bus.publish(
                DecisionDeleted(decision_id=decision_id, project_id=project_id)
            )

        return DeleteDecisionResponse(deleted=deleted, decision_id=decision_id)
