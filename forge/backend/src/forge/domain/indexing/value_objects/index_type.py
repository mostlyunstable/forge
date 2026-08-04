"""IndexType — type of indexing job."""

from enum import StrEnum


class IndexType(StrEnum):
    """Type of indexing operation."""

    FULL = "full"
    INCREMENTAL = "incremental"
    GIT_ONLY = "git_only"
    MEMORY_ONLY = "memory_only"
