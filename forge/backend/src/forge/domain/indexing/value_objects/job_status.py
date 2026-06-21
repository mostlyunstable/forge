"""JobStatus — lifecycle state of an indexing job."""
from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle states for an IndexJob."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
