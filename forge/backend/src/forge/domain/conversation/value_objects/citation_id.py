from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CitationId:
    value: uuid.UUID

    def __init__(self, value: uuid.UUID | None = None) -> None:
        object.__setattr__(self, "value", value or uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> CitationId:
        return cls(uuid.UUID(raw))

    def __str__(self) -> str:
        return str(self.value)
