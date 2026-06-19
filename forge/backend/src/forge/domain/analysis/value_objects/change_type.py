"""ChangeType — classification of file changes in a PR."""
from enum import Enum


class ChangeType(str, Enum):
    """How a file was modified."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
