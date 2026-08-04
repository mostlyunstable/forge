"""UpdateBugUseCase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from forge.domain.memory.events import BugReopened, BugResolved
from forge.domain.memory.exceptions import BugNotFoundError
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.shared.events import IEventBus


@dataclass
class UpdateBugRequest:
    """Input DTO for updating a bug."""

    bug_id: str
    title: str | None = None
    problem: str | None = None
    root_cause: str | None = None
    solution: str | None = None
    affected_files: list[str] | None = None
    severity: str | None = None
    resolved: bool | None = None


@dataclass
class UpdateBugResponse:
    """Output DTO after updating a bug."""

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


class UpdateBugUseCase:
    """Updates an existing bug record."""

    def __init__(
        self,
        bug_repo: IBugRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._bug_repo = bug_repo
        self._event_bus = event_bus

    async def execute(self, request: UpdateBugRequest) -> UpdateBugResponse:
        bug = await self._bug_repo.get_by_id(BugId.from_string(request.bug_id))
        if not bug:
            raise BugNotFoundError(request.bug_id)

        was_resolved = bug.resolved

        if request.title is not None:
            bug.title = request.title
        if request.problem is not None:
            bug.problem = request.problem
        if request.root_cause is not None:
            bug.root_cause = request.root_cause
        if request.solution is not None:
            bug.solution = request.solution
        if request.affected_files is not None:
            bug.affected_files = request.affected_files
        if request.severity is not None:
            bug.severity = request.severity
        if request.resolved is not None:
            if request.resolved and not was_resolved:
                bug.resolved = True
                bug.resolved_at = datetime.now(UTC)
            elif not request.resolved and was_resolved:
                bug.mark_unresolved()

        saved = await self._bug_repo.save(bug)

        if self._event_bus:
            if request.resolved is not None and request.resolved and not was_resolved:
                await self._event_bus.publish(
                    BugResolved(bug_id=str(saved.id), project_id=str(saved.project_id))
                )
            elif request.resolved is not None and not request.resolved and was_resolved:
                await self._event_bus.publish(
                    BugReopened(bug_id=str(saved.id), project_id=str(saved.project_id))
                )

        return UpdateBugResponse(
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
