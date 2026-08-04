"""Unit tests for risk calculator and recommendations."""

from forge.application.analysis.recommendations import build_summary, generate_recommendations
from forge.application.analysis.risk_calculator import calculate_risk
from forge.domain.analysis.entities.change_entry import ChangeEntry
from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import HistoricalContext, RelatedBug
from forge.domain.analysis.entities.risk_assessment import RiskAssessment
from forge.domain.analysis.value_objects.change_type import ChangeType
from forge.domain.analysis.value_objects.risk_level import RiskLevel


class TestRiskCalculator:
    def test_low_risk(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(
                    file_path="tests/test_foo.py",
                    change_type=ChangeType.ADDED,
                    lines_added=10,
                    is_test_file=True,
                ),
            ]
        )
        impact = DependencyImpact()
        history = HistoricalContext()
        risk = calculate_risk(cs, impact, history)
        assert risk.score < 50
        assert risk.level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_high_risk_domain_changes(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(
                    file_path="src/forge/domain/entities/project.py",
                    change_type=ChangeType.MODIFIED,
                    lines_added=100,
                    lines_removed=50,
                    is_core_module=True,
                ),
                ChangeEntry(
                    file_path="src/forge/domain/value_objects/id.py",
                    change_type=ChangeType.MODIFIED,
                    lines_added=50,
                    lines_removed=20,
                    is_core_module=True,
                ),
            ]
        )
        impact = DependencyImpact(
            directly_affected=["a.py", "b.py"],
            reverse_affected=["c.py", "d.py", "e.py"],
            affected_layers=["domain", "infrastructure"],
        )
        history = HistoricalContext(
            related_bugs=[
                RelatedBug(
                    id="1",
                    title="Bug",
                    root_cause="X",
                    solution="Y",
                    severity="high",
                    resolved=False,
                )
            ]
        )
        risk = calculate_risk(cs, impact, history)
        assert risk.score >= 40
        assert len(risk.factors) == 7

    def test_cycle_increases_risk(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(file_path="a.py", change_type=ChangeType.MODIFIED),
            ]
        )
        impact = DependencyImpact(cycle_detected=True)
        history = HistoricalContext()
        risk = calculate_risk(cs, impact, history)
        cycle_factor = [f for f in risk.factors if f.name == "dependency_cycles"][0]
        assert cycle_factor.score == 100


class TestRecommendations:
    def test_domain_change_recommendation(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(
                    file_path="src/forge/domain/entities/project.py",
                    change_type=ChangeType.MODIFIED,
                ),
            ]
        )
        impact = DependencyImpact()
        history = HistoricalContext()
        risk = RiskAssessment(score=30, level=RiskLevel.LOW)
        recs = generate_recommendations(cs, impact, history, risk)
        domain_recs = [r for r in recs if r.area == "Domain Layer"]
        assert len(domain_recs) == 1

    def test_no_tests_recommendation(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(
                    file_path="src/forge/domain/entities/x.py", change_type=ChangeType.MODIFIED
                ),
            ]
        )
        impact = DependencyImpact()
        history = HistoricalContext()
        risk = RiskAssessment(score=30, level=RiskLevel.LOW)
        recs = generate_recommendations(cs, impact, history, risk)
        test_recs = [r for r in recs if r.area == "Test Coverage"]
        assert len(test_recs) == 1

    def test_high_risk_recommendation(self):
        cs = ChangeSet(entries=[ChangeEntry(file_path="a.py", change_type=ChangeType.MODIFIED)])
        impact = DependencyImpact()
        history = HistoricalContext()
        risk = RiskAssessment(score=80, level=RiskLevel.CRITICAL)
        recs = generate_recommendations(cs, impact, history, risk)
        risk_recs = [r for r in recs if r.area == "Overall Risk"]
        assert len(risk_recs) == 1
        assert risk_recs[0].priority == "critical"

    def test_historical_bugs_recommendation(self):
        cs = ChangeSet(entries=[ChangeEntry(file_path="a.py", change_type=ChangeType.MODIFIED)])
        impact = DependencyImpact()
        history = HistoricalContext(
            related_bugs=[
                RelatedBug(
                    id="1", title="B", root_cause="X", solution="Y", severity="high", resolved=False
                )
            ]
        )
        risk = RiskAssessment(score=30, level=RiskLevel.LOW)
        recs = generate_recommendations(cs, impact, history, risk)
        bug_recs = [r for r in recs if r.area == "Historical Bugs"]
        assert len(bug_recs) == 1
        assert bug_recs[0].priority == "high"


class TestBuildSummary:
    def test_basic_summary(self):
        cs = ChangeSet(
            entries=[
                ChangeEntry(file_path="a.py", change_type=ChangeType.ADDED, lines_added=10),
            ]
        )
        impact = DependencyImpact(directly_affected=["a.py"])
        risk = RiskAssessment(score=25, level=RiskLevel.MEDIUM)
        summary = build_summary(cs, impact, risk)
        assert "1 file(s)" in summary
        assert "10 additions" in summary
        assert "25/100" in summary

    def test_cycle_warning(self):
        cs = ChangeSet(entries=[ChangeEntry(file_path="a.py", change_type=ChangeType.MODIFIED)])
        impact = DependencyImpact(cycle_detected=True)
        risk = RiskAssessment(score=50, level=RiskLevel.HIGH)
        summary = build_summary(cs, impact, risk)
        assert "WARNING" in summary
