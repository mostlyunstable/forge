"""Unit tests for the analysis domain model."""
import pytest
from uuid import uuid4

from forge.domain.analysis.value_objects.analysis_id import AnalysisId
from forge.domain.analysis.value_objects.change_type import ChangeType
from forge.domain.analysis.value_objects.risk_level import RiskLevel
from forge.domain.analysis.entities.change_entry import ChangeEntry
from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import HistoricalContext
from forge.domain.analysis.entities.risk_assessment import RiskAssessment, RiskFactor
from forge.domain.analysis.entities.analysis_report import AnalysisReport


class TestAnalysisId:
    def test_creates_uuid_when_none(self):
        aid = AnalysisId()
        assert aid.value is not None

    def test_from_string(self):
        raw = str(uuid4())
        aid = AnalysisId.from_string(raw)
        assert str(aid) == raw

    def test_str(self):
        aid = AnalysisId()
        assert str(aid) == str(aid.value)


class TestChangeType:
    def test_values(self):
        assert ChangeType.ADDED == "added"
        assert ChangeType.MODIFIED == "modified"
        assert ChangeType.DELETED == "deleted"
        assert ChangeType.RENAMED == "renamed"


class TestRiskLevel:
    def test_from_score_low(self):
        assert RiskLevel.from_score(10) == RiskLevel.LOW

    def test_from_score_medium(self):
        assert RiskLevel.from_score(30) == RiskLevel.MEDIUM

    def test_from_score_high(self):
        assert RiskLevel.from_score(60) == RiskLevel.HIGH

    def test_from_score_critical(self):
        assert RiskLevel.from_score(80) == RiskLevel.CRITICAL

    def test_boundary_values(self):
        assert RiskLevel.from_score(0) == RiskLevel.LOW
        assert RiskLevel.from_score(24) == RiskLevel.LOW
        assert RiskLevel.from_score(25) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(49) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(50) == RiskLevel.HIGH
        assert RiskLevel.from_score(74) == RiskLevel.HIGH
        assert RiskLevel.from_score(75) == RiskLevel.CRITICAL
        assert RiskLevel.from_score(100) == RiskLevel.CRITICAL


class TestChangeEntry:
    def test_net_lines(self):
        entry = ChangeEntry(file_path="a.py", change_type=ChangeType.MODIFIED, lines_added=10, lines_removed=3)
        assert entry.net_lines == 7

    def test_module_path_domain(self):
        entry = ChangeEntry(file_path="backend/src/forge/domain/projects/entities/project.py", change_type=ChangeType.MODIFIED)
        assert "domain" in entry.module_path

    def test_is_test_file(self):
        entry = ChangeEntry(file_path="tests/test_something.py", change_type=ChangeType.ADDED, is_test_file=True)
        assert entry.is_test_file is True

    def test_is_core_module(self):
        entry = ChangeEntry(file_path="src/forge/domain/entities/x.py", change_type=ChangeType.MODIFIED, is_core_module=True)
        assert entry.is_core_module is True


class TestChangeSet:
    def test_properties(self):
        entries = [
            ChangeEntry(file_path="a.py", change_type=ChangeType.ADDED, lines_added=10, lines_removed=0),
            ChangeEntry(file_path="b.py", change_type=ChangeType.MODIFIED, lines_added=5, lines_removed=3),
            ChangeEntry(file_path="test_a.py", change_type=ChangeType.ADDED, is_test_file=True, lines_added=20, lines_removed=0),
        ]
        cs = ChangeSet(entries=entries)
        assert cs.total_files == 3
        assert cs.total_added == 35
        assert cs.total_removed == 3
        assert len(cs.added_files) == 2
        assert len(cs.modified_files) == 1
        assert len(cs.test_files) == 1
        assert cs.has_api_changes is False

    def test_empty_changeset(self):
        cs = ChangeSet()
        assert cs.total_files == 0
        assert cs.unique_modules == []


class TestDependencyImpact:
    def test_blast_radius_no_cycle(self):
        impact = DependencyImpact(
            directly_affected=["a.py"],
            transitively_affected=["b.py", "c.py"],
            reverse_affected=["d.py"],
        )
        # 1*3 + 2*2 + 1*4 = 11
        assert impact.blast_radius == 11
        assert impact.total_affected_modules == 4

    def test_blast_radius_with_cycle(self):
        impact = DependencyImpact(cycle_detected=True)
        assert impact.blast_radius == 20

    def test_empty_impact(self):
        impact = DependencyImpact()
        assert impact.blast_radius == 0
        assert impact.total_affected_modules == 0


class TestHistoricalContext:
    def test_properties(self):
        from forge.domain.analysis.entities.historical_context import RelatedBug, RelatedDecision

        ctx = HistoricalContext(
            related_decisions=[RelatedDecision(id="1", title="ADR-1", decision="Use X", status="accepted")],
            related_bugs=[
                RelatedBug(id="1", title="Bug 1", root_cause="Y", solution="Z", severity="high", resolved=False),
                RelatedBug(id="2", title="Bug 2", root_cause="A", solution="B", severity="low", resolved=True),
            ],
        )
        assert ctx.total_related_items == 3
        assert ctx.has_related_bugs is True
        assert ctx.has_related_decisions is True
        assert ctx.unresolved_bugs_count == 1


class TestRiskAssessment:
    def test_compute_level(self):
        r = RiskAssessment(score=60)
        assert r.compute_level() == RiskLevel.HIGH

    def test_critical_factors(self):
        r = RiskAssessment(factors=[
            RiskFactor(name="a", weight=1, score=80, reason="high"),
            RiskFactor(name="b", weight=1, score=30, reason="low"),
        ])
        assert len(r.critical_factors) == 1
        assert r.critical_factors[0].name == "a"


class TestAnalysisReport:
    def test_create(self):
        report = AnalysisReport.create(project_id="proj-123", pr_number=42, title="Test PR")
        assert report.project_id == "proj-123"
        assert report.pr_number == 42
        assert report.title == "Test PR"
        assert report.id is not None

    def test_properties(self):
        report = AnalysisReport.create(project_id="proj-1")
        assert report.risk_level == RiskLevel.LOW
        assert report.risk_score == 0
        assert report.blast_radius == 0
