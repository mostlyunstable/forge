"""Domain exceptions for the Memory module."""


class DecisionNotFoundError(Exception):
    """Raised when a decision cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Decision not found: {identifier}")


class BugNotFoundError(Exception):
    """Raised when a bug cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Bug not found: {identifier}")


class PreferenceNotFoundError(Exception):
    """Raised when a preference cannot be found."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Preference not found: {key}")


class MemoryNotFoundError(Exception):
    """Raised when a memory cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Memory not found: {identifier}")
