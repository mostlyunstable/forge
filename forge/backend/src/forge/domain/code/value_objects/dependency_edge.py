"""DependencyEdge value object."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.code.value_objects.dependency_type import DependencyType


@dataclass(frozen=True)
class DependencyEdge:
    """Represents a directed edge in the dependency graph."""

    source_file: str
    source_name: str
    target_file: str
    target_name: str
    dependency_type: DependencyType
    line_number: int

    def __post_init__(self) -> None:
        if not self.source_file:
            raise ValueError("source_file cannot be empty")
        if not self.target_file:
            raise ValueError("target_file cannot be empty")
        if self.line_number < 0:
            raise ValueError("line_number must be non-negative")
