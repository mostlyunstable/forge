"""DeveloperPreference entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.memory.value_objects.preference_key import PreferenceKey


@dataclass
class DeveloperPreference:
    """Records a developer preference with confidence tracking."""

    key: PreferenceKey
    value: str
    confidence: float = 0.5
    evidence_count: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def strengthen(self, new_value: str, boost: float = 0.05) -> None:
        """Increase confidence when evidence supports this preference."""
        self.value = new_value
        self.confidence = min(0.99, self.confidence + boost)
        self.evidence_count += 1
        self.updated_at = datetime.now(UTC)

    @classmethod
    def create(cls, key: str, value: str, confidence: float = 0.5) -> DeveloperPreference:
        return cls(
            key=PreferenceKey(key),
            value=value,
            confidence=confidence,
        )
