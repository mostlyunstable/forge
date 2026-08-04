"""TechStack value object."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TechStack:
    """Immutable collection of technologies used in a project."""

    technologies: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_list(cls, items: list[str]) -> TechStack:
        return cls(frozenset(item.strip().lower() for item in items if item.strip()))

    def __len__(self) -> int:
        return len(self.technologies)

    def __iter__(self):  # noqa: ANN204
        return iter(self.technologies)
