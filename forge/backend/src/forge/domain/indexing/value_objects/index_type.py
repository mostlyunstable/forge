"""IndexType — type of indexing job."""
from enum import Enum


class IndexType(str, Enum):
    """Type of indexing operation."""

    FULL = "full"
    INCREMENTAL = "incremental"
    GIT_ONLY = "git_only"
    MEMORY_ONLY = "memory_only"
