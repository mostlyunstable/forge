"""GetDecisionUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.exceptions import DecisionNotFoundError
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.value_objects.decision_id import DecisionId


@dataclass
class GetDecisionResponse:
    """Output DTO for a single decision."""

    id: str
    project_id: str
    title: str
    decision: str
    reason: str
    alternatives: list[str]
    status: str
    created_at: str


class GetDecisionUseCase:
    """Retrieves a single decision by ID."""

    def __init__(self, decision_repo: IDecisionRepository) -> None:
        self._decision_repo = decision_repo

    async def execute(self, decision_id: str) -> GetDecisionResponse:
        decision = await self._decision_repo.get_by_id(DecisionId.from_string(decision_id))
        if not decision:
            raise DecisionNotFoundError(decision_id)

        return GetDecisionResponse(
            id=str(decision.id),
            project_id=str(decision.project_id),
            title=decision.title,
            decision=decision.decision,
            reason=decision.reason,
            alternatives=decision.alternatives,
            status=decision.status,
            created_at=decision.created_at.isoformat(),
        )
