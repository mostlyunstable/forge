"""Domain exceptions for the Projects module."""


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Project not found: {identifier}")
        self.identifier = identifier


class ProjectAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate project."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Project already exists: {name}")
        self.name = name
