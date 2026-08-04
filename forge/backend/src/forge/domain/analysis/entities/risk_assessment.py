"""RiskAssessment — computed risk for a PR."""

from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.analysis.value_objects.risk_level import RiskLevel


@dataclass
class RiskFactor:
    """A single risk factor contributing to the overall score."""

    name: str
    weight: int
    score: int
    reason: str

    @property
    def weighted_score(self) -> int:
        return self.weight * self.score


@dataclass
class RiskAssessment:
    """Aggregated risk assessment for a PR."""

    score: int = 0
    level: RiskLevel = RiskLevel.LOW
    factors: list[RiskFactor] = field(default_factory=list)

    def compute_level(self) -> RiskLevel:
        """Derive risk level from score."""
        self.level = RiskLevel.from_score(self.score)
        return self.level

    @property
    def critical_factors(self) -> list[RiskFactor]:
        """Factors with high individual scores."""
        return [f for f in self.factors if f.score >= 70]

    @property
    def summary(self) -> str:
        """Human-readable risk summary."""
        if not self.factors:
            return "No risk factors computed."
        parts = [f"{f.name}: {f.score}/100" for f in self.factors]
        return f"Overall: {self.score}/100 ({self.level.value}). Factors: {'; '.join(parts)}"
