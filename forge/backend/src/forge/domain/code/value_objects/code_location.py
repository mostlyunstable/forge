"""CodeLocation value objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilePath:
    """Normalized file path within a repository."""

    value: str

    def __init__(self, value: str) -> None:
        normalized = value.strip().lstrip("./")
        object.__setattr__(self, "value", normalized)

    @property
    def extension(self) -> str:
        if "." in self.value:
            return self.value.rsplit(".", 1)[-1]
        return ""

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LineRange:
    """Inclusive start/end line pair."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("start must be >= 1")
        if self.end < self.start:
            raise ValueError("end must be >= start")

    @property
    def length(self) -> int:
        return self.end - self.start + 1
