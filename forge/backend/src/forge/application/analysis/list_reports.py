"""ListAnalysisReportsUseCase — lists analysis reports for a project."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.analysis.repository_contracts.analysis_repository import (
    IAnalysisReportRepository,
)
from forge.domain.analysis.value_objects.analysis_id import AnalysisId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.application.analysis.get_report import GetAnalysisReportUseCase


@dataclass
class ListAnalysisReportsRequest:
    """Input DTO for listing reports."""

    project_id: str
    skip: int = 0
    limit: int = 20


class ListAnalysisReportsUseCase:
    """Lists analysis reports for a project."""

    def __init__(self, report_repo: IAnalysisReportRepository) -> None:
        self._report_repo = report_repo
        self._get_use_case = GetAnalysisReportUseCase(report_repo)

    async def execute(self, request: ListAnalysisReportsRequest) -> list[dict]:
        """Returns list of report summaries for a project."""
        pid = ProjectId.from_string(request.project_id)
        reports = await self._report_repo.get_by_project(
            pid, skip=request.skip, limit=request.limit
        )
        total = await self._report_repo.count_by_project(pid)

        return [
            {
                "id": str(r.id),
                "project_id": r.project_id,
                "pr_number": r.pr_number,
                "title": r.title,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level.value,
                "files_changed": r.change_set.total_files,
                "blast_radius": r.blast_radius,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ]
