"""DecisionId value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from forge.domain.memory.value_objects.memory_id import MemoryId


@dataclass(frozen=True)
class DecisionId(MemoryId):
    """Unique identifier for an ArchitectureDecision."""

    def __init__(self, value: uuid.UUID | None = None) -> None:
        super().__init__(value)
