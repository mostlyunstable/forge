"""GetFileEntriesUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.code.repository_contracts.code_repository import ICodeRepository
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class FileEntryDetail:
    """Detailed code entry information."""

    name: str
    entry_type: str
    content: str
    language: str
    start_line: int
    end_line: int
    metadata: dict


@dataclass
class GetFileEntriesResponse:
    """Output DTO for file entries."""

    file_path: str
    entries: list[FileEntryDetail]
    total: int


class GetFileEntriesUseCase:
    """Retrieves all code entries for a specific file."""

    def __init__(self, code_repo: ICodeRepository) -> None:
        self._code_repo = code_repo

    async def execute(
        self,
        project_id: str,
        file_path: str,
    ) -> GetFileEntriesResponse:
        entries = await self._code_repo.get_by_file_path(ProjectId.from_string(project_id), file_path)

        details = [
            FileEntryDetail(
                name=e.name,
                entry_type=e.entry_type.value,
                content=e.content,
                language=e.language,
                start_line=e.lines.start,
                end_line=e.lines.end,
                metadata=e.metadata,
            )
            for e in entries
        ]

        return GetFileEntriesResponse(
            file_path=file_path,
            entries=details,
            total=len(details),
        )
