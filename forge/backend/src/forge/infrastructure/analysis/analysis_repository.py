"""AnalysisReportRepository — persists analysis reports to the database."""
from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.analysis.entities.analysis_report import (
    AnalysisReport,
    ReviewRecommendation,
)
from forge.domain.analysis.entities.change_entry import ChangeEntry
from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import (
    HistoricalContext,
    RelatedBug,
    RelatedCommit,
    RelatedDecision,
    RelatedPreference,
)
from forge.domain.analysis.entities.risk_assessment import RiskAssessment, RiskFactor
from forge.domain.analysis.repository_contracts.analysis_repository import (
    IAnalysisReportRepository,
)
from forge.domain.analysis.value_objects.analysis_id import AnalysisId
from forge.domain.analysis.value_objects.change_type import ChangeType
from forge.domain.analysis.value_objects.risk_level import RiskLevel
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.analysis_report_model import AnalysisReportModel


class AnalysisReportRepository(IAnalysisReportRepository):
    """SQLAlchemy implementation of IAnalysisReportRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, report_id: AnalysisId) -> Optional[AnalysisReport]:
        result = await self._session.execute(
            select(AnalysisReportModel).where(
                AnalysisReportModel.id == str(report_id.value)
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(
        self, project_id: ProjectId, skip: int = 0, limit: int = 20
    ) -> list[AnalysisReport]:
        result = await self._session.execute(
            select(AnalysisReportModel)
            .where(AnalysisReportModel.project_id == str(project_id.value))
            .order_by(AnalysisReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_pr(
        self, project_id: ProjectId, pr_number: int
    ) -> Optional[AnalysisReport]:
        result = await self._session.execute(
            select(AnalysisReportModel).where(
                AnalysisReportModel.project_id == str(project_id.value),
                AnalysisReportModel.pr_number == pr_number,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, report: AnalysisReport) -> AnalysisReport:
        existing = await self._session.get(
            AnalysisReportModel, str(report.id.value)
        )
        if existing:
            existing.title = report.title
            existing.summary = report.summary
            existing.change_set = self._serialize_change_set(report.change_set)
            existing.dependency_impact = self._serialize_dep_impact(report.dependency_impact)
            existing.historical_context = self._serialize_history(report.historical_context)
            existing.risk_assessment = self._serialize_risk(report.risk_assessment)
            existing.recommendations = self._serialize_recommendations(report.recommendations)
            await self._session.flush()
            return self._to_domain(existing)

        model = AnalysisReportModel(
            id=str(report.id.value),
            project_id=report.project_id,
            pr_number=report.pr_number,
            title=report.title,
            summary=report.summary,
            change_set=self._serialize_change_set(report.change_set),
            dependency_impact=self._serialize_dep_impact(report.dependency_impact),
            historical_context=self._serialize_history(report.historical_context),
            risk_assessment=self._serialize_risk(report.risk_assessment),
            recommendations=self._serialize_recommendations(report.recommendations),
            created_at=report.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, report_id: AnalysisId) -> bool:
        result = await self._session.execute(
            select(AnalysisReportModel).where(
                AnalysisReportModel.id == str(report_id.value)
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    async def count_by_project(self, project_id: ProjectId) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(AnalysisReportModel).where(
                AnalysisReportModel.project_id == str(project_id.value)
            )
        )
        return result.scalar() or 0

    # --- Serialization helpers ---

    def _serialize_change_set(self, cs: ChangeSet) -> dict:
        return {
            "entries": [
                {
                    "file_path": e.file_path,
                    "change_type": e.change_type.value,
                    "lines_added": e.lines_added,
                    "lines_removed": e.lines_removed,
                    "is_test_file": e.is_test_file,
                    "is_core_module": e.is_core_module,
                    "language": e.language,
                }
                for e in cs.entries
            ]
        }

    def _serialize_dep_impact(self, di: DependencyImpact) -> dict:
        return {
            "directly_affected": di.directly_affected,
            "transitively_affected": di.transitively_affected,
            "reverse_affected": di.reverse_affected,
            "import_edges": di.import_edges,
            "cycle_detected": di.cycle_detected,
            "affected_layers": di.affected_layers,
        }

    def _serialize_history(self, h: HistoricalContext) -> dict:
        return {
            "related_decisions": [
                {"id": d.id, "title": d.title, "decision": d.decision, "status": d.status, "relevance_reason": d.relevance_reason}
                for d in h.related_decisions
            ],
            "related_bugs": [
                {"id": b.id, "title": b.title, "root_cause": b.root_cause, "solution": b.solution, "severity": b.severity, "resolved": b.resolved, "relevance_reason": b.relevance_reason}
                for b in h.related_bugs
            ],
            "related_commits": [
                {"sha": c.sha, "message": c.message, "classification": c.classification, "timestamp": c.timestamp, "relevance_reason": c.relevance_reason}
                for c in h.related_commits
            ],
            "related_preferences": [
                {"key": p.key, "value": p.value, "confidence": p.confidence, "relevance_reason": p.relevance_reason}
                for p in h.related_preferences
            ],
        }

    def _serialize_risk(self, r: RiskAssessment) -> dict:
        return {
            "score": r.score,
            "level": r.level.value,
            "factors": [
                {"name": f.name, "weight": f.weight, "score": f.score, "reason": f.reason}
                for f in r.factors
            ],
        }

    def _serialize_recommendations(self, recs: list[ReviewRecommendation]) -> list[dict]:
        return [
            {"area": r.area, "priority": r.priority, "description": r.description, "files": r.files}
            for r in recs
        ]

    # --- Deserialization helpers ---

    def _to_domain(self, model: AnalysisReportModel) -> AnalysisReport:
        cs_data = model.change_set or {}
        entries = [
            ChangeEntry(
                file_path=e["file_path"],
                change_type=ChangeType(e.get("change_type", "modified")),
                lines_added=e.get("lines_added", 0),
                lines_removed=e.get("lines_removed", 0),
                is_test_file=e.get("is_test_file", False),
                is_core_module=e.get("is_core_module", False),
                language=e.get("language", ""),
            )
            for e in cs_data.get("entries", [])
        ]
        change_set = ChangeSet(entries=entries)

        di_data = model.dependency_impact or {}
        dep_impact = DependencyImpact(
            directly_affected=di_data.get("directly_affected", []),
            transitively_affected=di_data.get("transitively_affected", []),
            reverse_affected=di_data.get("reverse_affected", []),
            import_edges=di_data.get("import_edges", []),
            cycle_detected=di_data.get("cycle_detected", False),
            affected_layers=di_data.get("affected_layers", []),
        )

        h_data = model.historical_context or {}
        history = HistoricalContext(
            related_decisions=[
                RelatedDecision(
                    id=d["id"], title=d["title"], decision=d["decision"],
                    status=d["status"], relevance_reason=d.get("relevance_reason", ""),
                )
                for d in h_data.get("related_decisions", [])
            ],
            related_bugs=[
                RelatedBug(
                    id=b["id"], title=b["title"], root_cause=b["root_cause"],
                    solution=b["solution"], severity=b["severity"],
                    resolved=b.get("resolved", True),
                    relevance_reason=b.get("relevance_reason", ""),
                )
                for b in h_data.get("related_bugs", [])
            ],
            related_commits=[
                RelatedCommit(
                    sha=c["sha"], message=c["message"],
                    classification=c["classification"],
                    timestamp=c.get("timestamp", ""),
                    relevance_reason=c.get("relevance_reason", ""),
                )
                for c in h_data.get("related_commits", [])
            ],
            related_preferences=[
                RelatedPreference(
                    key=p["key"], value=p["value"],
                    confidence=p.get("confidence", 0.0),
                    relevance_reason=p.get("relevance_reason", ""),
                )
                for p in h_data.get("related_preferences", [])
            ],
        )

        r_data = model.risk_assessment or {}
        risk = RiskAssessment(
            score=r_data.get("score", 0),
            level=RiskLevel(r_data.get("level", "low")),
            factors=[
                RiskFactor(
                    name=f["name"], weight=f["weight"],
                    score=f["score"], reason=f["reason"],
                )
                for f in r_data.get("factors", [])
            ],
        )

        recs_data = model.recommendations or []
        recommendations = [
            ReviewRecommendation(
                area=r["area"], priority=r["priority"],
                description=r["description"], files=r.get("files", []),
            )
            for r in recs_data
        ]

        return AnalysisReport(
            id=AnalysisId(UUID(model.id)),
            project_id=model.project_id,
            pr_number=model.pr_number,
            title=model.title or "",
            summary=model.summary or "",
            change_set=change_set,
            dependency_impact=dep_impact,
            historical_context=history,
            risk_assessment=risk,
            recommendations=recommendations,
            created_at=model.created_at,
        )
