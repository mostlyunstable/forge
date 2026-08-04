"""DeleteBugUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.events import BugDeleted
from forge.domain.memory.exceptions import BugNotFoundError
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.shared.events import IEventBus


@dataclass
class DeleteBugResponse:
    """Output DTO after deleting a bug."""

    deleted: bool
    bug_id: str


class DeleteBugUseCase:
    """Deletes a bug record."""

    def __init__(
        self,
        bug_repo: IBugRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._bug_repo = bug_repo
        self._event_bus = event_bus

    async def execute(self, bug_id: str) -> DeleteBugResponse:
        bug = await self._bug_repo.get_by_id(BugId.from_string(bug_id))
        if not bug:
            raise BugNotFoundError(bug_id)

        project_id = str(bug.project_id)
        deleted = await self._bug_repo.delete(BugId.from_string(bug_id))

        if self._event_bus and deleted:
            await self._event_bus.publish(BugDeleted(bug_id=bug_id, project_id=project_id))

        return DeleteBugResponse(deleted=deleted, bug_id=bug_id)
