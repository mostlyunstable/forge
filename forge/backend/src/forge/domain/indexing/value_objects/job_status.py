"""JobStatus — lifecycle state of an indexing job."""

from enum import StrEnum


class JobStatus(StrEnum):
    """Lifecycle states for an IndexJob."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
