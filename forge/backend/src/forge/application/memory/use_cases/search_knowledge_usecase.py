"""SearchKnowledgeUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.projects.value_objects.project_id import ProjectId

@dataclass
class SearchKnowledgeRequest:
    query: str
    project_id: str
    limit: int = 10

@dataclass
class KnowledgeResult:
    id: str
    title: str
    summary: str
    type: str

@dataclass
class SearchKnowledgeResponse:
    results: list[KnowledgeResult]
    query: str

class SearchKnowledgeUseCase:
    """Searches engineering knowledge (basic implementation)."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self._memory_repo = memory_repo

    async def execute(self, request: SearchKnowledgeRequest) -> SearchKnowledgeResponse:
        project_id = ProjectId(request.project_id)
        
        # Basic implementation filtering in memory
        all_memories = await self._memory_repo.get_by_project(project_id)
        
        query_lower = request.query.lower()
        matched = []
        
        for mem in all_memories:
            # Skip archived and superseded versions
            if mem.archived_at is not None or mem.superseded_by_id is not None:
                continue
                
            if (query_lower in mem.title.lower() or 
                query_lower in mem.summary.lower() or 
                query_lower in mem.body.lower()):
                matched.append(mem)
                
            if len(matched) >= request.limit:
                break
                
        results = [
            KnowledgeResult(
                id=str(m.id.value),
                title=m.title,
                summary=m.summary,
                type=m.memory_type,
            ) for m in matched
        ]

        return SearchKnowledgeResponse(
            results=results,
            query=request.query
        )
