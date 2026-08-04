"""Risk calculation logic for PR analysis."""

from __future__ import annotations

from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import HistoricalContext
from forge.domain.analysis.entities.risk_assessment import RiskAssessment, RiskFactor


def calculate_risk(
    change_set: ChangeSet,
    dep_impact: DependencyImpact,
    history: HistoricalContext,
) -> RiskAssessment:
    """Calculate the overall risk score for a PR."""
    factors: list[RiskFactor] = []

    # Factor 1: Core module changes (weight: 3)
    core_pct = (len(change_set.core_module_files) / max(change_set.total_files, 1)) * 100
    factors.append(
        RiskFactor(
            name="core_module_changes",
            weight=3,
            score=min(int(core_pct), 100),
            reason=f"{len(change_set.core_module_files)} of {change_set.total_files} files are core modules",
        )
    )

    # Factor 2: Blast radius (weight: 3)
    blast = dep_impact.blast_radius
    blast_score = min(blast * 2, 100)
    factors.append(
        RiskFactor(
            name="blast_radius",
            weight=3,
            score=blast_score,
            reason=f"Blast radius score: {blast} ({dep_impact.total_affected_modules} modules affected)",
        )
    )

    # Factor 3: Historical bug density (weight: 2)
    bug_count = len(history.related_bugs)
    unresolved = history.unresolved_bugs_count
    bug_score = min((bug_count * 15) + (unresolved * 25), 100)
    factors.append(
        RiskFactor(
            name="historical_bug_density",
            weight=2,
            score=bug_score,
            reason=f"{bug_count} related bugs found ({unresolved} unresolved)",
        )
    )

    # Factor 4: Test coverage (weight: 2)
    test_count = len(change_set.test_files)
    non_test_count = change_set.total_files - test_count
    if non_test_count > 0:
        test_ratio = test_count / non_test_count
        test_score = max(0, int((1 - min(test_ratio, 1.0)) * 100))
    else:
        test_score = 0
    factors.append(
        RiskFactor(
            name="test_coverage",
            weight=2,
            score=test_score,
            reason=f"{test_count} test files, {non_test_count} non-test files changed",
        )
    )

    # Factor 5: Scale of change (weight: 1)
    total_lines = change_set.total_added + change_set.total_removed
    scale_score = min(int(total_lines / 10), 100)
    factors.append(
        RiskFactor(
            name="change_scale",
            weight=1,
            score=scale_score,
            reason=f"{total_lines} total lines changed ({change_set.total_added}+ {change_set.total_removed}-)",
        )
    )

    # Factor 6: Layer boundary crossing (weight: 2)
    layers = set(dep_impact.affected_layers)
    boundary_score = min(len(layers) * 25, 100)
    factors.append(
        RiskFactor(
            name="layer_boundaries",
            weight=2,
            score=boundary_score,
            reason=f"{len(layers)} architectural layers affected: {', '.join(sorted(layers))}",
        )
    )

    # Factor 7: Cycle detection (weight: 1)
    cycle_score = 100 if dep_impact.cycle_detected else 0
    factors.append(
        RiskFactor(
            name="dependency_cycles",
            weight=1,
            score=cycle_score,
            reason="Circular dependency detected" if dep_impact.cycle_detected else "No cycles",
        )
    )

    # Compute weighted average
    total_weight = sum(f.weight for f in factors)
    if total_weight > 0:
        weighted_sum = sum(f.weighted_score for f in factors)
        score = min(int(weighted_sum / total_weight), 100)
    else:
        score = 0

    assessment = RiskAssessment(score=score, factors=factors)
    assessment.compute_level()
    return assessment
