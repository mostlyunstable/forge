"""GitHistoryIngester — ingests git history into the knowledge graph."""
from __future__ import annotations

import structlog
from uuid import UUID

from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.repository_contracts.index_job_repository import IIndexJobRepository
from forge.domain.indexing.ports.git_commit_parser import IGitCommitParser
from forge.application.indexing.memory_extractor import MemoryExtractor

logger = structlog.get_logger()


class GitHistoryIngester:
    """Ingests git commit history and extracts knowledge."""

    def __init__(
        self,
        job_repo: IIndexJobRepository,
        commit_parser: IGitCommitParser,
        memory_extractor: MemoryExtractor,
    ) -> None:
        self._job_repo = job_repo
        self._commit_parser = commit_parser
        self._memory_extractor = memory_extractor

    async def ingest(
        self,
        job: IndexJob,
        repo_path: str,
        since_commit: str | None = None,
        max_commits: int = 1000,
    ) -> dict:
        """Ingest git history from a repository.

        Returns summary of ingestion.
        """
        commits = self._commit_parser.get_commit_history(
            repo_path, since=since_commit, limit=max_commits
        )

        if not commits:
            logger.info("no_new_commits", repo_path=repo_path, since=since_commit)
            return {"commits_ingested": 0, "candidates_extracted": 0}

        total_candidates = 0
        for i, commit in enumerate(commits):
            try:
                # Update progress
                job.update_progress(
                    phase="git_ingestion",
                    files_done=i + 1,
                    files_total=len(commits),
                )

                # Extract candidates from commit message
                candidates = self._memory_extractor.extract_from_commit_message(
                    job_id=job.id,
                    commit_sha=commit.sha,
                    message=commit.message,
                    author_name=commit.author_name,
                    files_changed=commit.files_changed,
                )

                total_candidates += len(candidates)

                # Log progress periodically
                if (i + 1) % 100 == 0:
                    logger.info(
                        "git_ingestion_progress",
                        commits_done=i + 1,
                        total=len(commits),
                        candidates=total_candidates,
                    )

            except Exception as e:
                job.log_error(
                    file_path=f"commit:{commit.sha}",
                    error=str(e),
                    phase="git_ingestion",
                )
                logger.warning(
                    "commit_ingestion_error",
                    sha=commit.sha,
                    error=str(e),
                )

        return {
            "commits_ingested": len(commits),
            "candidates_extracted": total_candidates,
        }
