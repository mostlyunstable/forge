# mypy: disable-error-code="assignment, arg-type"
"""MemoryContextSearcher — searches historical context for PR analysis."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.analysis.ports import IContextSearcher
from forge.infrastructure.repositories.bug_repository import BugRepository
from forge.infrastructure.repositories.commit_repository import CommitRepository
from forge.infrastructure.repositories.decision_repository import DecisionRepository

logger = structlog.get_logger()


class MemoryContextSearcher(IContextSearcher):
    """Searches decisions, bugs, and commits for historical context.

    Composes existing repositories to find related items.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_related_decisions(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Find decisions relevant to the query."""
        try:
            repo = DecisionRepository(self._session)
            decisions = await repo.search_by_title(query)
            return [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "decision": d.decision,
                    "status": d.status,
                }
                for d in decisions
            ]
        except Exception as e:
            logger.warning("context_search_decisions_error", error=str(e))
            return []

    async def search_related_bugs(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Find bugs relevant to the query."""
        try:
            repo = BugRepository(self._session)
            bugs = await repo.search_by_problem(query)
            return [
                {
                    "id": str(b.id),
                    "title": b.title,
                    "root_cause": b.root_cause,
                    "solution": b.solution,
                    "severity": b.severity,
                    "resolved": b.resolved,
                }
                for b in bugs
            ]
        except Exception as e:
            logger.warning("context_search_bugs_error", error=str(e))
            return []

    async def search_related_commits(
        self, project_id: str, file_paths: list[str], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find commits that previously touched the same files."""
        try:
            from uuid import UUID

            from forge.domain.projects.value_objects.project_id import ProjectId

            repo = CommitRepository(self._session)
            pid = ProjectId(UUID(project_id))
            commits = await repo.get_recent(pid, limit=limit)

            # Filter commits that touched any of the changed files
            result = []
            for c in commits:
                if any(fp in c.files_changed for fp in file_paths):
                    result.append(
                        {
                            "sha": c.sha.value,
                            "message": c.message,
                            "classification": c.classification.value,
                            "timestamp": c.timestamp.isoformat(),
                        }
                    )
            return result[:limit]
        except Exception as e:
            logger.warning("context_search_commits_error", error=str(e))
            return []
