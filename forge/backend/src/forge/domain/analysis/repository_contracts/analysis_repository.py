"""IAnalysisReportRepository — persistence contract for analysis reports."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.analysis.entities.analysis_report import AnalysisReport
from forge.domain.analysis.value_objects.analysis_id import AnalysisId
from forge.domain.projects.value_objects.project_id import ProjectId


class IAnalysisReportRepository(ABC):
    """Abstract repository for analysis report persistence."""

    @abstractmethod
    async def get_by_id(self, report_id: AnalysisId) -> Optional[AnalysisReport]:
        """Retrieve a report by its ID."""

    @abstractmethod
    async def get_by_project(
        self, project_id: ProjectId, skip: int = 0, limit: int = 20
    ) -> list[AnalysisReport]:
        """List reports for a project, newest first."""

    @abstractmethod
    async def get_by_pr(
        self, project_id: ProjectId, pr_number: int
    ) -> Optional[AnalysisReport]:
        """Retrieve the report for a specific PR."""

    @abstractmethod
    async def save(self, report: AnalysisReport) -> AnalysisReport:
        """Persist an analysis report."""

    @abstractmethod
    async def delete(self, report_id: AnalysisId) -> bool:
        """Delete a report."""

    @abstractmethod
    async def count_by_project(self, project_id: ProjectId) -> int:
        """Count total reports for a project."""
