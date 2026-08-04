"""Domain events for the analysis bounded context."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class PRAnalyzed(DomainEvent):
    """Emitted when a PR analysis is completed."""

    report_id: str = ""
    project_id: str = ""
    pr_number: int = 0
    risk_score: int = 0
    risk_level: str = "low"
    files_changed: int = 0

    @property
    def event_type(self) -> str:
        return "analysis.pr_analyzed"


@dataclass(frozen=True)
class RiskThresholdExceeded(DomainEvent):
    """Emitted when a PR's risk score exceeds the threshold."""

    report_id: str = ""
    project_id: str = ""
    pr_number: int = 0
    risk_score: int = 0
    risk_level: str = "critical"
    threshold: int = 75

    @property
    def event_type(self) -> str:
        return "analysis.risk_threshold_exceeded"
