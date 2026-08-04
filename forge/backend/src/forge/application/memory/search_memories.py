"""SearchMemoriesUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository


@dataclass
class MemoryResult:
    """A single memory search result."""

    type: str
    id: str
    title: str
    content: str
    score: float


@dataclass
class SearchMemoriesResponse:
    """Output DTO for memory search results."""

    results: list[MemoryResult]
    query: str
    total: int


class SearchMemoriesUseCase:
    """Searches across decisions and bugs by text query."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        bug_repo: IBugRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._decision_repo = decision_repo
        self._bug_repo = bug_repo
        self._project_repo = project_repo

    async def execute(
        self,
        query: str,
        project_id: str | None = None,
    ) -> SearchMemoriesResponse:
        results: list[MemoryResult] = []

        decisions = await self._decision_repo.search_by_title(query)
        for d in decisions:
            if project_id and str(d.project_id.value) != project_id:
                continue
            results.append(
                MemoryResult(
                    type="decision",
                    id=str(d.id),
                    title=d.title,
                    content=d.decision,
                    score=1.0,
                )
            )

        bugs = await self._bug_repo.search_by_problem(query)
        for b in bugs:
            if project_id and str(b.project_id.value) != project_id:
                continue
            results.append(
                MemoryResult(
                    type="bug",
                    id=str(b.id),
                    title=b.title,
                    content=b.solution,
                    score=1.0,
                )
            )

        return SearchMemoriesResponse(
            results=results,
            query=query,
            total=len(results),
        )
