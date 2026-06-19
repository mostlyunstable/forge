"""Domain exceptions for the Code Intelligence module."""


class CodeEntryNotFoundError(Exception):
    """Raised when a code entry cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Code entry not found: {identifier}")


class IndexingError(Exception):
    """Raised when repository indexing fails."""

    def __init__(self, repo_path: str, reason: str) -> None:
        super().__init__(f"Indexing failed for {repo_path}: {reason}")
        self.repo_path = repo_path
        self.reason = reason
