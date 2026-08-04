"""ChangeType — classification of file changes in a PR."""

from enum import StrEnum


class ChangeType(StrEnum):
    """How a file was modified."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
