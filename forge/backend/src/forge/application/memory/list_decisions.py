"""ListDecisionsUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.exceptions import ProjectNotFoundError


@dataclass
class DecisionSummary:
    """Summary of a decision for list view."""

    id: str
    title: str
    decision: str
    status: str
    created_at: str


@dataclass
class ListDecisionsResponse:
    """Output DTO for listing decisions."""

    decisions: list[DecisionSummary]
    total: int
    project_id: str


class ListDecisionsUseCase:
    """Lists all decisions for a project."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._decision_repo = decision_repo
        self._project_repo = project_repo

    async def execute(self, project_id: str, skip: int = 0, limit: int = 100) -> ListDecisionsResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(project_id))
        if not project:
            raise ProjectNotFoundError(project_id)

        decisions = await self._decision_repo.get_by_project(ProjectId.from_string(project_id))
        total = len(decisions)
        paginated = decisions[skip:skip + limit]

        return ListDecisionsResponse(
            decisions=[
                DecisionSummary(
                    id=str(d.id),
                    title=d.title,
                    decision=d.decision,
                    status=d.status,
                    created_at=d.created_at.isoformat(),
                )
                for d in paginated
            ],
            total=total,
            project_id=project_id,
        )
