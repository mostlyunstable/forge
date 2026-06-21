"""Exceptions for the indexing bounded context."""


class IndexJobNotFoundError(Exception):
    """Raised when an indexing job is not found."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Index job not found: {identifier}")


class IndexingError(Exception):
    """Raised when indexing fails."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Indexing failed: {reason}")


class CheckpointCorruptedError(Exception):
    """Raised when a checkpoint is corrupted and cannot be resumed."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Checkpoint corrupted for job: {job_id}")
