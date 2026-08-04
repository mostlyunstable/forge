"""AnalysisReport — aggregate root for PR analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import HistoricalContext
from forge.domain.analysis.entities.risk_assessment import RiskAssessment
from forge.domain.analysis.value_objects.analysis_id import AnalysisId
from forge.domain.analysis.value_objects.risk_level import RiskLevel


@dataclass
class ReviewRecommendation:
    """A specific recommendation for the PR reviewer."""

    area: str
    priority: str
    description: str
    files: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Root aggregate for a PR Context & Impact Analysis.

    This is the core domain entity. It captures:
    - What changed (ChangeSet)
    - What modules are impacted (DependencyImpact)
    - What historical context exists (HistoricalContext)
    - How risky the change is (RiskAssessment)
    - What reviewers should focus on (recommendations)
    """

    id: AnalysisId
    project_id: str
    pr_number: int | None = None
    title: str = ""
    summary: str = ""
    change_set: ChangeSet = field(default_factory=ChangeSet)
    dependency_impact: DependencyImpact = field(default_factory=DependencyImpact)
    historical_context: HistoricalContext = field(default_factory=HistoricalContext)
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    recommendations: list[ReviewRecommendation] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def risk_level(self) -> RiskLevel:
        return self.risk_assessment.level

    @property
    def risk_score(self) -> int:
        return self.risk_assessment.score

    @property
    def blast_radius(self) -> int:
        return self.dependency_impact.blast_radius

    @classmethod
    def create(
        cls,
        project_id: str,
        pr_number: int | None = None,
        title: str = "",
    ) -> AnalysisReport:
        return cls(
            id=AnalysisId(),
            project_id=project_id,
            pr_number=pr_number,
            title=title,
        )
