"""Analysis routes — PR Context & Impact Analysis API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.search.graph_adapter import SQLiteDependencyGraph
from forge.infrastructure.analysis.git_diff_provider import GitDiffProvider
from forge.infrastructure.analysis.memory_context_searcher import MemoryContextSearcher
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.analysis.analyze_pr import AnalyzePRUseCase, AnalyzePRRequest
from forge.application.analysis.get_report import GetAnalysisReportUseCase
from forge.application.analysis.list_reports import (
    ListAnalysisReportsUseCase,
    ListAnalysisReportsRequest,
)
from forge.domain.analysis.exceptions import AnalysisReportNotFoundError, AnalysisError
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.presentation.deps import get_session, get_project_repo, get_analysis_report_repo
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.analysis_schemas import (
    AnalyzePRRequest as AnalyzePRSchema,
    AnalyzePRResponse,
    AnalysisReportSummary,
    ListAnalysisReportsResponse,
    AnalysisReportDetail,
    RecommendationResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/pr", response_model=AnalyzePRResponse, status_code=201)
async def analyze_pr(
    body: AnalyzePRSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """Analyze a pull request for context and impact."""
    report_repo = get_analysis_report_repo(session)
    project_repo = get_project_repo(session)
    dep_graph = SQLiteDependencyGraph()
    diff_provider = GitDiffProvider()
    context_searcher = MemoryContextSearcher(session)

    use_case = AnalyzePRUseCase(
        report_repo=report_repo,
        project_repo=project_repo,
        dependency_graph=dep_graph,
        diff_provider=diff_provider,
        context_searcher=context_searcher,
        event_bus=event_bus,
    )

    result = await use_case.execute(
        AnalyzePRRequest(
            project_id=body.project_id,
            pr_number=body.pr_number,
            base_sha=body.base_sha,
            head_sha=body.head_sha,
            title=body.title,
        )
    )

    return AnalyzePRResponse(
        report_id=result.report_id,
        project_id=result.project_id,
        pr_number=result.pr_number,
        title=result.title,
        summary=result.summary,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        blast_radius=result.blast_radius,
        files_changed=result.files_changed,
        directly_affected=result.directly_affected,
        transitively_affected=result.transitively_affected,
        reverse_affected=result.reverse_affected,
        related_decisions=result.related_decisions,
        related_bugs=result.related_bugs,
        related_commits=result.related_commits,
        recommendations=[
            RecommendationResponse(**r) for r in result.recommendations
        ],
    )


@router.get("/reports", response_model=ListAnalysisReportsResponse)
async def list_reports(
    project_id: str = Query(...),
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """List analysis reports for a project."""
    report_repo = get_analysis_report_repo(session)
    use_case = ListAnalysisReportsUseCase(report_repo)

    reports = await use_case.execute(
        ListAnalysisReportsRequest(
            project_id=project_id,
            skip=skip,
            limit=limit,
        )
    )

    try:
        from forge.domain.projects.value_objects.project_id import ProjectId
        from uuid import UUID
        total = await report_repo.count_by_project(ProjectId(UUID(project_id)))
    except ValueError:
        total = 0

    return ListAnalysisReportsResponse(
        reports=[AnalysisReportSummary(**r) for r in reports],
        total=total,
        project_id=project_id,
    )


@router.get("/reports/{report_id}", response_model=AnalysisReportDetail)
async def get_report(
    report_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    """Get a specific analysis report."""
    report_repo = get_analysis_report_repo(session)
    use_case = GetAnalysisReportUseCase(report_repo)

    result = await use_case.execute(report_id)

    return AnalysisReportDetail(
        id=result.id,
        project_id=result.project_id,
        pr_number=result.pr_number,
        title=result.title,
        summary=result.summary,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        blast_radius=result.blast_radius,
        files_changed=result.files_changed,
        directly_affected=result.directly_affected,
        transitively_affected=result.transitively_affected,
        reverse_affected=result.reverse_affected,
        related_decisions=result.related_decisions,
        related_bugs=result.related_bugs,
        related_commits=result.related_commits,
        recommendations=[
            RecommendationResponse(**r) for r in result.recommendations
        ],
        created_at=result.created_at,
    )
