"""IndexRepositoryUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.code.repository_contracts.code_repository import ICodeRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.code.events import CodeEntriesBatchIndexed, CodeIndexCleared
from forge.domain.shared.events import IEventBus


@dataclass
class IndexRepositoryRequest:
    """Input DTO for indexing a repository."""

    project_id: str
    repo_path: str


@dataclass
class IndexRepositoryResponse:
    """Output DTO after indexing."""

    files_indexed: int
    entries_found: int
    entry_types: dict[str, int]


class IndexRepositoryUseCase:
    """Indexes a repository by parsing code and storing entries.
    Delegates actual parsing to the code indexer port (infrastructure).
    """

    def __init__(
        self,
        project_repo: IProjectRepository,
        code_repo: ICodeRepository,
        code_indexer,  # ICodeIndexer port
        event_bus: IEventBus | None = None,
    ) -> None:
        self._project_repo = project_repo
        self._code_repo = code_repo
        self._code_indexer = code_indexer
        self._event_bus = event_bus

    async def execute(self, request: IndexRepositoryRequest) -> IndexRepositoryResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        await self._code_repo.delete_by_project(project.id)

        if self._event_bus:
            await self._event_bus.publish(
                CodeIndexCleared(project_id=str(project.id))
            )

        entries = await self._code_indexer.index(project.id, request.repo_path)

        entry_types: dict[str, int] = {}
        for entry in entries:
            entry_types[entry.entry_type.value] = entry_types.get(entry.entry_type.value, 0) + 1

        files_indexed = len({str(e.file_path) for e in entries})

        if self._event_bus and entries:
            await self._event_bus.publish(
                CodeEntriesBatchIndexed(
                    project_id=str(project.id),
                    entry_count=len(entries),
                    repo_path=request.repo_path,
                )
            )

        return IndexRepositoryResponse(
            files_indexed=files_indexed,
            entries_found=len(entries),
            entry_types=entry_types,
        )
