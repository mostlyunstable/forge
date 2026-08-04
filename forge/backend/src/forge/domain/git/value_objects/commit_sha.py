"""CommitSha value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommitSha:
    """Git commit SHA hash."""

    value: str

    def __init__(self, value: str) -> None:
        normalized = value.strip()
        if len(normalized) < 7:
            raise ValueError("CommitSha must be at least 7 characters")
        object.__setattr__(self, "value", normalized)

    @property
    def short(self) -> str:
        return self.value[:8]

    def __str__(self) -> str:
        return self.value
