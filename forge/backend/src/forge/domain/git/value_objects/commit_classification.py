"""CommitClassification value object."""

from enum import StrEnum


class CommitClassification(StrEnum):
    """Classification of a git commit by its purpose."""

    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    SECURITY = "security"
    OTHER = "other"
