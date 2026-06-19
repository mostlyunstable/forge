"""PreferenceKey value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreferenceKey:
    """Unique key identifying a developer preference."""

    value: str

    def __init__(self, value: str) -> None:
        normalized = value.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("PreferenceKey cannot be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
