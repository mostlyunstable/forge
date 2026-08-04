"""Project aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack


@dataclass
class Project:
    """Project aggregate root. Owns project lifecycle and metadata."""

    id: ProjectId
    name: str
    description: str
    stack: TechStack
    goals: list[str] = field(default_factory=list)
    status: str = "active"
    repository_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_description(self, description: str) -> None:
        self.description = description
        self._touch()

    def update_stack(self, stack: TechStack) -> None:
        self.stack = stack
        self._touch()

    def add_goal(self, goal: str) -> None:
        if goal not in self.goals:
            self.goals.append(goal)
            self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        stack: TechStack,
        goals: list[str] | None = None,
        repository_url: str | None = None,
    ) -> Project:
        return cls(
            id=ProjectId(),
            name=name,
            description=description,
            stack=stack,
            goals=goals or [],
            repository_url=repository_url,
        )
