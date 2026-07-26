"""UpdateMemoryUseCase."""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy

from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.memory.exceptions import MemoryNotFoundError

@dataclass
class UpdateMemoryRequest:
    memory_id: str
    title: str | None = None
    summary: str | None = None
    body: str | None = None

@dataclass
class UpdateMemoryResponse:
    memory_id: str
    previous_version_id: str
    version_number: int

class UpdateMemoryUseCase:
    """Updates a memory by creating a new version in the chain."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self._memory_repo = memory_repo

    async def execute(self, request: UpdateMemoryRequest) -> UpdateMemoryResponse:
        memory_id = MemoryId(request.memory_id)
        existing_memory = await self._memory_repo.get_by_id(memory_id)
        
        if not existing_memory:
            raise MemoryNotFoundError(f"Memory with ID {request.memory_id} not found.")

        # Create a new version
        new_memory = deepcopy(existing_memory)
        new_memory.id = MemoryId()
        new_memory.version_number += 1
        new_memory.previous_version_id = existing_memory.id
        new_memory.superseded_by_id = None

        if request.title or request.summary or request.body:
            new_memory.update_content(
                title=request.title or existing_memory.title,
                summary=request.summary or existing_memory.summary,
                body=request.body or existing_memory.body
            )

        existing_memory.superseded_by_id = new_memory.id
        
        # Save both
        await self._memory_repo.save(existing_memory)
        await self._memory_repo.save(new_memory)

        return UpdateMemoryResponse(
            memory_id=str(new_memory.id.value),
            previous_version_id=str(existing_memory.id.value),
            version_number=new_memory.version_number
        )
