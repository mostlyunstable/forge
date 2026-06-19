"""AnalyzePRUseCase — orchestrates full PR context and impact analysis."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from forge.domain.analysis.entities.analysis_report import AnalysisReport
from forge.domain.analysis.entities.change_entry import ChangeEntry
from forge.domain.analysis.entities.change_set import ChangeSet
from forge.domain.analysis.entities.dependency_impact import DependencyImpact
from forge.domain.analysis.entities.historical_context import (
    HistoricalContext,
    RelatedBug,
    RelatedCommit,
    RelatedDecision,
)
from forge.domain.analysis.exceptions import AnalysisError
from forge.domain.analysis.repository_contracts.analysis_repository import (
    IAnalysisReportRepository,
)
from forge.domain.analysis.value_objects.change_type import ChangeType
from forge.domain.analysis.events import PRAnalyzed, RiskThresholdExceeded
from forge.domain.analysis.ports import IDiffProvider, IContextSearcher
from forge.domain.code.repository_contracts.dependency_graph import IDependencyGraph
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.shared.events import IEventBus
from forge.application.analysis.risk_calculator import calculate_risk
from forge.application.analysis.recommendations import generate_recommendations, build_summary

logger = structlog.get_logger()

MAX_FILES_LIMIT = 500
RISK_THRESHOLD = 75


@dataclass
class AnalyzePRRequest:
    """Input DTO for PR analysis."""

    project_id: str
    pr_number: int | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    title: str = ""


@dataclass
class AnalyzePRResponse:
    """Output DTO after PR analysis."""

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
    recommendations: list[dict]


class AnalyzePRUseCase:
    """Orchestrates the full PR analysis pipeline."""

    def __init__(
        self,
        report_repo: IAnalysisReportRepository,
        project_repo: IProjectRepository,
        dependency_graph: IDependencyGraph,
        diff_provider: IDiffProvider,
        context_searcher: IContextSearcher,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._report_repo = report_repo
        self._project_repo = project_repo
        self._dep_graph = dependency_graph
        self._diff_provider = diff_provider
        self._context_searcher = context_searcher
        self._event_bus = event_bus

    async def execute(self, request: AnalyzePRRequest) -> AnalyzePRResponse:
        await self._validate_project(request.project_id)
        diff_data = await self._fetch_diff(request)
        change_set = self._build_change_set(diff_data)

        if change_set.total_files > MAX_FILES_LIMIT:
            raise AnalysisError(
                f"Diff contains {change_set.total_files} files, exceeding limit of {MAX_FILES_LIMIT}."
            )

        dep_impact = await self._compute_dependency_impact(request.project_id, change_set)
        history = await self._gather_historical_context(request.project_id, change_set)
        risk = calculate_risk(change_set, dep_impact, history)
        recommendations = generate_recommendations(change_set, dep_impact, history, risk)
        summary = build_summary(change_set, dep_impact, risk)

        report = self._create_report(request, diff_data, change_set, dep_impact, history, risk, recommendations, summary)
        saved = await self._report_repo.save(report)
        await self._emit_events(request, risk, change_set, saved)

        logger.info(
            "pr_analysis_completed",
            report_id=str(saved.id),
            project_id=request.project_id,
            risk_score=risk.score,
        )

        return self._build_response(saved, summary)

    async def _validate_project(self, project_id: str) -> None:
        try:
            pid = ProjectId(UUID(project_id))
        except ValueError:
            raise ProjectNotFoundError(project_id)
        project = await self._project_repo.get_by_id(pid)
        if not project:
            raise ProjectNotFoundError(project_id)

    async def _fetch_diff(self, request: AnalyzePRRequest) -> dict:
        pid = ProjectId(UUID(request.project_id))
        if request.pr_number is not None:
            return await self._diff_provider.get_pr_diff(pid, request.pr_number)
        elif request.base_sha and request.head_sha:
            return await self._diff_provider.get_commit_diff(pid, request.base_sha, request.head_sha)
        raise AnalysisError("Either pr_number or (base_sha, head_sha) must be provided.")

    def _build_change_set(self, diff_data: dict) -> ChangeSet:
        entries = []
        for file_info in diff_data.get("files", []):
            try:
                change_type = ChangeType(file_info.get("change_type", "modified"))
            except ValueError:
                change_type = ChangeType.MODIFIED

            file_path = file_info.get("file_path", "")
            entries.append(
                ChangeEntry(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=file_info.get("additions", 0),
                    lines_removed=file_info.get("deletions", 0),
                    is_test_file="test" in file_path.lower() or file_path.endswith("_test.py"),
                    is_core_module=any(l in file_path for l in ("domain/", "application/", "infrastructure/")),
                    language=file_info.get("language", ""),
                )
            )
        return ChangeSet(entries=entries)

    async def _compute_dependency_impact(self, project_id: str, change_set: ChangeSet) -> DependencyImpact:
        import asyncio

        pid = ProjectId(UUID(project_id))
        impact = DependencyImpact(directly_affected=[e.file_path for e in change_set.entries])
        affected_layers: set[str] = set()

        async def _query_file(file_path: str) -> tuple[list, list]:
            imports_result = []
            dependents_result = []
            try:
                imports_result = await self._dep_graph.get_imports(pid, file_path)
            except Exception as e:
                logger.warning("dep_graph_imports_error", file_path=file_path, error=str(e))
            try:
                dependents_result = await self._dep_graph.get_dependents(pid, file_path)
            except Exception as e:
                logger.warning("dep_graph_dependents_error", file_path=file_path, error=str(e))
            return imports_result, dependents_result

        # Run all queries in parallel with bounded concurrency
        sem = asyncio.Semaphore(50)

        async def _bounded_query(fp: str):
            async with sem:
                return fp, await _query_file(fp)

        results = await asyncio.gather(
            *[_bounded_query(fp) for fp in impact.directly_affected],
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning("dep_graph_query_failed", error=str(result))
                continue
            file_path, (imports, dependents) = result
            for edge in imports:
                if edge.target_file not in impact.transitively_affected:
                    impact.transitively_affected.append(edge.target_file)
                impact.import_edges.append({"source": edge.source_file, "target": edge.target_file, "type": edge.dependency_type.value})
            for edge in dependents:
                if edge.source_file not in impact.reverse_affected:
                    impact.reverse_affected.append(edge.source_file)

        try:
            cycles = await self._dep_graph.detect_cycles(pid)
            impact.cycle_detected = len(cycles) > 0
        except Exception as e:
            logger.warning("dep_graph_cycle_detection_error", error=str(e))

        all_affected = set(impact.directly_affected + impact.transitively_affected + impact.reverse_affected)
        for path in all_affected:
            for layer in ("domain", "application", "infrastructure", "presentation", "tests"):
                if f"{layer}/" in path:
                    affected_layers.add(layer)
        impact.affected_layers = sorted(affected_layers)
        return impact

    async def _gather_historical_context(self, project_id: str, change_set: ChangeSet) -> HistoricalContext:
        search_terms = self._extract_search_terms(change_set)
        context = HistoricalContext()

        for term in search_terms[:5]:
            for d in await self._context_searcher.search_related_decisions(project_id, term):
                rd = RelatedDecision(id=d.get("id", ""), title=d.get("title", ""), decision=d.get("decision", ""), status=d.get("status", ""), relevance_reason=f"Related to '{term}'")
                if not any(x.id == rd.id for x in context.related_decisions):
                    context.related_decisions.append(rd)

            for b in await self._context_searcher.search_related_bugs(project_id, term):
                rb = RelatedBug(id=b.get("id", ""), title=b.get("title", ""), root_cause=b.get("root_cause", ""), solution=b.get("solution", ""), severity=b.get("severity", ""), resolved=b.get("resolved", True), relevance_reason=f"Related to '{term}'")
                if not any(x.id == rb.id for x in context.related_bugs):
                    context.related_bugs.append(rb)

        file_paths = [e.file_path for e in change_set.entries]
        for c in await self._context_searcher.search_related_commits(project_id, file_paths, limit=10):
            rc = RelatedCommit(sha=c.get("sha", ""), message=c.get("message", ""), classification=c.get("classification", ""), timestamp=str(c.get("timestamp", "")), relevance_reason="Previously modified same file(s)")
            if not any(x.sha == rc.sha for x in context.related_commits):
                context.related_commits.append(rc)

        return context

    def _extract_search_terms(self, change_set: ChangeSet) -> list[str]:
        seen: set[str] = set()
        terms: list[str] = []
        for entry in change_set.entries:
            name = entry.file_path.split("/")[-1].split(".")[0]
            if name and name not in ("__init__", "conftest") and name not in seen:
                seen.add(name)
                terms.append(name)
        return terms[:10]

    def _create_report(self, request, diff_data, change_set, dep_impact, history, risk, recommendations, summary) -> AnalysisReport:
        report = AnalysisReport.create(project_id=request.project_id, pr_number=request.pr_number, title=diff_data.get("title", request.title))
        report.summary = summary
        report.change_set = change_set
        report.dependency_impact = dep_impact
        report.historical_context = history
        report.risk_assessment = risk
        report.recommendations = recommendations
        return report

    async def _emit_events(self, request, risk, change_set, saved) -> None:
        if not self._event_bus:
            return
        await self._event_bus.publish(PRAnalyzed(report_id=str(saved.id), project_id=request.project_id, pr_number=request.pr_number or 0, risk_score=risk.score, risk_level=risk.level.value, files_changed=change_set.total_files))
        if risk.score >= RISK_THRESHOLD:
            await self._event_bus.publish(RiskThresholdExceeded(report_id=str(saved.id), project_id=request.project_id, pr_number=request.pr_number or 0, risk_score=risk.score, risk_level=risk.level.value, threshold=RISK_THRESHOLD))

    def _build_response(self, saved: AnalysisReport, summary: str) -> AnalyzePRResponse:
        return AnalyzePRResponse(
            report_id=str(saved.id),
            project_id=saved.project_id,
            pr_number=saved.pr_number,
            title=saved.title,
            summary=summary,
            risk_score=saved.risk_score,
            risk_level=saved.risk_level.value,
            blast_radius=saved.blast_radius,
            files_changed=saved.change_set.total_files,
            directly_affected=saved.dependency_impact.directly_affected,
            transitively_affected=saved.dependency_impact.transitively_affected,
            reverse_affected=saved.dependency_impact.reverse_affected,
            related_decisions=len(saved.historical_context.related_decisions),
            related_bugs=len(saved.historical_context.related_bugs),
            related_commits=len(saved.historical_context.related_commits),
            recommendations=[{"area": r.area, "priority": r.priority, "description": r.description, "files": r.files} for r in saved.recommendations],
        )
