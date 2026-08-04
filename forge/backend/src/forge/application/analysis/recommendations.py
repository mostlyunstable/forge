"""Recommendation generation for PR analysis."""

from __future__ import annotations

from forge.domain.analysis.entities.analysis_report import ReviewRecommendation
from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import HistoricalContext
from forge.domain.analysis.entities.risk_assessment import RiskAssessment


def generate_recommendations(
    change_set: ChangeSet,
    dep_impact: DependencyImpact,
    history: HistoricalContext,
    risk: RiskAssessment,
) -> list[ReviewRecommendation]:
    """Generate actionable reviewer recommendations."""
    recs: list[ReviewRecommendation] = []

    # Domain layer changes
    domain_files = [e for e in change_set.entries if "domain/" in e.file_path]
    if domain_files:
        recs.append(
            ReviewRecommendation(
                area="Domain Layer",
                priority="high",
                description=(
                    f"{len(domain_files)} domain files changed. "
                    "Review for adherence to DDD principles, entity invariants, "
                    "and value object immutability."
                ),
                files=[f.file_path for f in domain_files],
            )
        )

    # Historical bug correlation
    if history.has_related_bugs:
        recs.append(
            ReviewRecommendation(
                area="Historical Bugs",
                priority="high" if history.unresolved_bugs_count > 0 else "medium",
                description=(
                    f"{len(history.related_bugs)} related bugs found. "
                    f"{history.unresolved_bugs_count} are unresolved. "
                    "Review if changes address root causes."
                ),
                files=[],
            )
        )

    # Reverse dependencies
    if dep_impact.reverse_affected:
        recs.append(
            ReviewRecommendation(
                area="Downstream Impact",
                priority="high",
                description=(
                    f"{len(dep_impact.reverse_affected)} modules depend on changed code. "
                    "Run integration tests for all dependent modules."
                ),
                files=dep_impact.reverse_affected[:20],
            )
        )

    # Missing tests
    non_test_files = [e for e in change_set.entries if not e.is_test_file]
    test_files = change_set.test_files
    if non_test_files and not test_files:
        recs.append(
            ReviewRecommendation(
                area="Test Coverage",
                priority="medium",
                description=(
                    f"{len(non_test_files)} files changed with no test files included. "
                    "Consider adding or updating tests."
                ),
                files=[f.file_path for f in non_test_files[:10]],
            )
        )

    # Migration changes
    migration_files = [
        e for e in change_set.entries if "alembic" in e.file_path or "migration" in e.file_path
    ]
    if migration_files:
        recs.append(
            ReviewRecommendation(
                area="Database Migrations",
                priority="critical",
                description=(
                    "Migration files changed. Verify backward compatibility, "
                    "rollout strategy, and data integrity."
                ),
                files=[f.file_path for f in migration_files],
            )
        )

    # High risk score
    if risk.score >= 75:
        recs.append(
            ReviewRecommendation(
                area="Overall Risk",
                priority="critical",
                description=(
                    f"Risk score is {risk.score}/100 ({risk.level.value}). "
                    "This PR requires thorough review before merging."
                ),
                files=[],
            )
        )

    # Infrastructure changes
    infra_files = [e for e in change_set.entries if "infrastructure/" in e.file_path]
    if infra_files:
        recs.append(
            ReviewRecommendation(
                area="Infrastructure Layer",
                priority="medium",
                description=(
                    f"{len(infra_files)} infrastructure files changed. "
                    "Review repository implementations, external service adapters, "
                    "and database schema changes."
                ),
                files=[f.file_path for f in infra_files],
            )
        )

    return recs


def build_summary(
    change_set: ChangeSet,
    dep_impact: DependencyImpact,
    risk: RiskAssessment,
) -> str:
    """Build a human-readable executive summary."""
    parts = [
        f"This PR changes {change_set.total_files} file(s) "
        f"({change_set.total_added} additions, {change_set.total_removed} deletions).",
    ]

    if change_set.has_domain_changes:
        parts.append("It includes domain layer changes.")
    if change_set.has_infrastructure_changes:
        parts.append("It includes infrastructure layer changes.")
    if change_set.has_api_changes:
        parts.append("It includes API/schema changes.")

    affected = dep_impact.total_affected_modules
    if affected > 0:
        parts.append(
            f"{affected} module(s) are directly or transitively affected "
            f"(blast radius: {dep_impact.blast_radius})."
        )

    if dep_impact.cycle_detected:
        parts.append("WARNING: Circular dependency detected.")

    parts.append(f"Overall risk: {risk.score}/100 ({risk.level.value}).")

    return " ".join(parts)
