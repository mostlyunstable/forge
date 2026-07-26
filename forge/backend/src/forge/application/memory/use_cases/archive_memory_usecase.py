"""ArchiveMemoryUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.memory.exceptions import MemoryNotFoundError


@dataclass
class ArchiveMemoryRequest:
    memory_id: str


@dataclass
class ArchiveMemoryResponse:
    memory_id: str
    success: bool


class ArchiveMemoryUseCase:
    """Marks a memory as archived."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self._memory_repo = memory_repo

    async def execute(self, request: ArchiveMemoryRequest) -> ArchiveMemoryResponse:
        memory_id = MemoryId(request.memory_id)
        memory = await self._memory_repo.get_by_id(memory_id)
        
        if not memory:
            raise MemoryNotFoundError(f"Memory with ID {request.memory_id} not found.")

        memory.archive()
        await self._memory_repo.save(memory)

        return ArchiveMemoryResponse(
            memory_id=str(memory.id.value),
            success=True
        )
