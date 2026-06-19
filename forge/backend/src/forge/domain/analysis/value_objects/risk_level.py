"""RiskLevel — severity classification for analysis risk."""
from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: int) -> RiskLevel:
        """Map a 0-100 risk score to a risk level."""
        if score < 25:
            return cls.LOW
        if score < 50:
            return cls.MEDIUM
        if score < 75:
            return cls.HIGH
        return cls.CRITICAL
