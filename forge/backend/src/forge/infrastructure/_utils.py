"""Shared utilities for safe SQL pattern matching."""
from __future__ import annotations


def escape_like_pattern(query: str) -> str:
    """Escape special characters in SQL LIKE patterns.

    Prevents pattern injection where % and _ in user input
    cause unintended pattern matching.
    """
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
