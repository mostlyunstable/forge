"""MemoryId value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


from typing import Type, TypeVar

T = TypeVar("T", bound="MemoryId")

@dataclass(frozen=True)
class MemoryId:
    """Unique identifier for any persistent engineering Memory."""

    value: uuid.UUID

    def __init__(self, value: uuid.UUID | None = None) -> None:
        object.__setattr__(self, "value", value or uuid.uuid4())

    @classmethod
    def from_string(cls: Type[T], raw: str) -> T:
        return cls(uuid.UUID(raw))

    def __str__(self) -> str:
        return str(self.value)
