"""ProjectId value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectId:
    """Unique identifier for a Project. Immutable value object."""

    value: uuid.UUID

    def __init__(self, value: uuid.UUID | None = None) -> None:
        object.__setattr__(self, "value", value or uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> ProjectId:
        return cls(uuid.UUID(raw))

    def __str__(self) -> str:
        return str(self.value)
