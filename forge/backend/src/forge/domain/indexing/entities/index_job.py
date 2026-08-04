"""IndexJob — aggregate root for indexing operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.indexing.value_objects.job_status import JobStatus


@dataclass
class IndexJob:
    """Tracks a codebase indexing operation.

    Lifecycle: pending → running → completed/failed/cancelled

    Supports checkpointing for resumable indexing.
    """

    id: UUID
    project_id: UUID
    type: IndexType
    status: JobStatus = JobStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    error_log: list[dict] = field(default_factory=list)
    checkpoint: dict = field(default_factory=dict)
    state_hash: str = ""
    created_by: str = "api"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def start(self) -> None:
        """Transition to running state."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def complete(self, result: dict, state_hash: str) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.result = result
        self.state_hash = state_hash

    def fail(self, error: str, phase: str = "") -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.error_log.append(
            {
                "error": error,
                "phase": phase,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def cancel(self) -> None:
        """Cancel the job."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(UTC)

    def update_progress(self, phase: str, files_done: int, files_total: int) -> None:
        """Update progress tracking."""
        self.progress = {
            "current_phase": phase,
            "files_done": files_done,
            "files_total": files_total,
        }

    def save_checkpoint(self, checkpoint: dict) -> None:
        """Save checkpoint for resumable indexing."""
        self.checkpoint = checkpoint

    def log_error(self, file_path: str, error: str, phase: str = "") -> None:
        """Log a per-file error without failing the job."""
        self.error_log.append(
            {
                "file": file_path,
                "error": error,
                "phase": phase,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    @property
    def is_resumable(self) -> bool:
        """Check if job can be resumed from checkpoint."""
        return (
            self.status == JobStatus.FAILED
            and bool(self.checkpoint)
            and self.checkpoint.get("phase") != "complete"
        )

    @property
    def duration_seconds(self) -> float | None:
        """Return job duration in seconds, or None if not completed."""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds()

    @classmethod
    def create(
        cls,
        project_id: UUID,
        type: IndexType,
        created_by: str = "api",
    ) -> IndexJob:
        return cls(
            id=uuid4(),
            project_id=project_id,
            type=type,
            created_by=created_by,
        )
