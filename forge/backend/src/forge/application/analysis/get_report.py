"""GetAnalysisReportUseCase — retrieves analysis reports."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.analysis.entities.analysis_report import AnalysisReport
from forge.domain.analysis.exceptions import AnalysisReportNotFoundError
from forge.domain.analysis.repository_contracts.analysis_repository import (
    IAnalysisReportRepository,
)
from forge.domain.analysis.value_objects.analysis_id import AnalysisId


@dataclass
class GetAnalysisReportResponse:
    """Output DTO for a single analysis report."""

    id: str
    project_id: str
    pr_number: int | None
    title: str
    summary: str
    risk_score: int
    risk_level: str
    blast_radius: int
    files_changed: int
    directly_affected: list[str]
    transitively_affected: list[str]
    reverse_affected: list[str]
    related_decisions: int
    related_bugs: int
    related_commits: int
    recommendations: list[dict]
    created_at: str


@dataclass
class ListAnalysisReportsResponse:
    """Output DTO for listing analysis reports."""

    reports: list[GetAnalysisReportResponse]
    total: int
    project_id: str


class GetAnalysisReportUseCase:
    """Retrieves analysis reports by ID."""

    def __init__(self, report_repo: IAnalysisReportRepository) -> None:
        self._report_repo = report_repo

    async def execute(self, report_id: str) -> GetAnalysisReportResponse:
        try:
            aid = AnalysisId.from_string(report_id)
        except ValueError:
            raise AnalysisReportNotFoundError(report_id)
        report = await self._report_repo.get_by_id(aid)
        if not report:
            raise AnalysisReportNotFoundError(report_id)
        return self._to_response(report)

    def _to_response(self, report: AnalysisReport) -> GetAnalysisReportResponse:
        return GetAnalysisReportResponse(
            id=str(report.id),
            project_id=report.project_id,
            pr_number=report.pr_number,
            title=report.title,
            summary=report.summary,
            risk_score=report.risk_score,
            risk_level=report.risk_level.value,
            blast_radius=report.blast_radius,
            files_changed=report.change_set.total_files,
            directly_affected=report.dependency_impact.directly_affected,
            transitively_affected=report.dependency_impact.transitively_affected,
            reverse_affected=report.dependency_impact.reverse_affected,
            related_decisions=len(report.historical_context.related_decisions),
            related_bugs=len(report.historical_context.related_bugs),
            related_commits=len(report.historical_context.related_commits),
            recommendations=[
                {
                    "area": r.area,
                    "priority": r.priority,
                    "description": r.description,
                    "files": r.files,
                }
                for r in report.recommendations
            ],
            created_at=report.created_at.isoformat(),
        )
