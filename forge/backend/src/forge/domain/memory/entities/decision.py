"""ArchitectureDecision entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class ArchitectureDecision:
    """Records an architectural decision with rationale and alternatives."""

    id: DecisionId
    project_id: ProjectId
    title: str
    decision: str
    reason: str
    alternatives: list[str] = field(default_factory=list)
    status: str = "accepted"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_reason(self, reason: str) -> None:
        self.reason = reason

    def add_alternative(self, alternative: str) -> None:
        if alternative not in self.alternatives:
            self.alternatives.append(alternative)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        title: str,
        decision: str,
        reason: str,
        alternatives: list[str] | None = None,
    ) -> ArchitectureDecision:
        return cls(
            id=DecisionId(),
            project_id=project_id,
            title=title,
            decision=decision,
            reason=reason,
            alternatives=alternatives or [],
        )
