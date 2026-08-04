"""SearchCodeUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.code.repository_contracts.code_repository import ICodeRepository
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CodeEntryResult:
    """A single code search result."""

    id: str
    name: str
    entry_type: str
    file_path: str
    language: str
    start_line: int
    end_line: int


@dataclass
class SearchCodeResponse:
    """Output DTO for code search results."""

    results: list[CodeEntryResult]
    query: str
    total: int


class SearchCodeUseCase:
    """Searches code entries by name within a project."""

    def __init__(self, code_repo: ICodeRepository) -> None:
        self._code_repo = code_repo

    async def execute(
        self,
        query: str,
        project_id: str,
    ) -> SearchCodeResponse:
        entries = await self._code_repo.search_by_name(ProjectId.from_string(project_id), query)

        results = [
            CodeEntryResult(
                id=str(e.id),
                name=e.name,
                entry_type=e.entry_type.value,
                file_path=str(e.file_path),
                language=e.language,
                start_line=e.lines.start,
                end_line=e.lines.end,
            )
            for e in entries
        ]

        return SearchCodeResponse(
            results=results,
            query=query,
            total=len(results),
        )
