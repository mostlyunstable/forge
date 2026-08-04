"""Schemas for the analysis API."""

from pydantic import BaseModel, Field


class AnalyzePRRequest(BaseModel):
    """Request body for PR analysis."""

    project_id: str = Field(..., description="Project UUID")
    pr_number: int | None = Field(None, description="Pull request number")
    base_sha: str | None = Field(None, description="Base commit SHA")
    head_sha: str | None = Field(None, description="Head commit SHA")
    title: str = Field("", description="Optional PR title override")


class RecommendationResponse(BaseModel):
    """A single review recommendation."""

    area: str
    priority: str
    description: str
    files: list[str] = []


class AnalyzePRResponse(BaseModel):
    """Response from PR analysis."""

    report_id: str
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
    recommendations: list[RecommendationResponse]


class AnalysisReportSummary(BaseModel):
    """Summary of an analysis report for listing."""

    id: str
    project_id: str
    pr_number: int | None
    title: str
    risk_score: int
    risk_level: str
    files_changed: int
    blast_radius: int
    created_at: str


class ListAnalysisReportsResponse(BaseModel):
    """Response for listing analysis reports."""

    reports: list[AnalysisReportSummary]
    total: int
    project_id: str


class AnalysisReportDetail(BaseModel):
    """Full analysis report detail."""

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
    recommendations: list[RecommendationResponse]
    created_at: str
