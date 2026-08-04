"""ReindexDetector — determines when re-indexing is needed."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from forge.domain.indexing.repository_contracts.file_index_repository import IFileIndexRepository
from forge.domain.indexing.repository_contracts.index_job_repository import IIndexJobRepository


@dataclass
class ReindexReason:
    """Reason why re-indexing is needed."""

    needed: bool
    reason: str
    full_reindex: bool = False


class ReindexDetector:
    """Determines if re-indexing is needed and what type."""

    def __init__(
        self,
        job_repo: IIndexJobRepository,
        file_index_repo: IFileIndexRepository,
    ) -> None:
        self._job_repo = job_repo
        self._file_index_repo = file_index_repo

    async def check(
        self,
        project_id: UUID,
        current_files: dict[str, str],  # file_path → content_hash
        latest_commit: str | None = None,
    ) -> ReindexReason:
        """Check if re-indexing is needed.

        Args:
            project_id: Project to check
            current_files: Current file paths and their content hashes
            latest_commit: Latest commit SHA in the repo

        Returns:
            ReindexReason with whether re-indexing is needed and why
        """
        # Check if there are any previous jobs
        last_job = await self._job_repo.get_latest_completed(project_id)
        if not last_job:
            return ReindexReason(
                needed=True,
                reason="No previous indexing job found",
                full_reindex=True,
            )

        # Check if last job failed
        if last_job.status.value == "failed":
            if last_job.is_resumable:
                return ReindexReason(
                    needed=True,
                    reason=f"Previous job {last_job.id} failed, can resume",
                    full_reindex=False,
                )
            return ReindexReason(
                needed=True,
                reason=f"Previous job {last_job.id} failed, cannot resume",
                full_reindex=True,
            )

        # Check if state hash changed
        current_state_hash = self._compute_state_hash(current_files, latest_commit)
        if current_state_hash != last_job.state_hash:
            # Determine if incremental or full
            if latest_commit and last_job.checkpoint.get("last_commit_sha"):
                return ReindexReason(
                    needed=True,
                    reason=f"New commits since last index ({last_job.checkpoint.get('last_commit_sha', '')[:8]}..{latest_commit[:8]})",
                    full_reindex=False,
                )
            return ReindexReason(
                needed=True,
                reason="Project state changed since last index",
                full_reindex=True,
            )

        return ReindexReason(
            needed=False,
            reason="Project is up to date",
        )

    def _compute_state_hash(self, files: dict[str, str], latest_commit: str | None) -> str:
        """Compute a hash of the project state."""
        # Sort files for deterministic hashing
        sorted_files = sorted(files.items())
        content = f"{latest_commit or ''}:{':'.join(f'{k}:{v}' for k, v in sorted_files)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
