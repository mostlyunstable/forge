"""Domain exceptions for the Git Intelligence module."""


class CommitNotFoundError(Exception):
    """Raised when a commit cannot be found."""

    def __init__(self, sha: str) -> None:
        super().__init__(f"Commit not found: {sha}")
