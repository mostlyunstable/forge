"""TechStack value object."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class TechStack:
    """Immutable collection of technologies used in a project."""

    technologies: FrozenSet[str] = field(default_factory=frozenset)

    @classmethod
    def from_list(cls, items: list[str]) -> TechStack:
        return cls(frozenset(item.strip().lower() for item in items if item.strip()))

    def contains(self, technology: str) -> bool:
        return technology.lower() in self.technologies

    def add(self, technology: str) -> TechStack:
        return TechStack(self.technologies | {technology.lower()})

    def __len__(self) -> int:
        return len(self.technologies)

    def __iter__(self):  # noqa: ANN204
        return iter(self.technologies)
