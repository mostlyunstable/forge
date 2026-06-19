"""GetBugUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.memory.exceptions import BugNotFoundError


@dataclass
class GetBugResponse:
    """Output DTO for a single bug."""

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


class GetBugUseCase:
    """Retrieves a single bug by ID."""

    def __init__(self, bug_repo: IBugRepository) -> None:
        self._bug_repo = bug_repo

    async def execute(self, bug_id: str) -> GetBugResponse:
        bug = await self._bug_repo.get_by_id(BugId.from_string(bug_id))
        if not bug:
            raise BugNotFoundError(bug_id)

        return GetBugResponse(
            id=str(bug.id),
            project_id=str(bug.project_id),
            title=bug.title,
            problem=bug.problem,
            root_cause=bug.root_cause,
            solution=bug.solution,
            affected_files=bug.affected_files,
            severity=bug.severity,
            resolved=bug.resolved,
            created_at=bug.created_at.isoformat(),
        )
