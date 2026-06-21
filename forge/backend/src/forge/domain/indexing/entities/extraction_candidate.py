"""ExtractionCandidate — a piece of knowledge extracted from code or commits."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class ExtractionCandidate:
    """A candidate decision, bug, or preference extracted from code/commits.

    Extraction is two-phase:
    1. Extract candidates (no side effects, idempotent)
    2. Accept candidates into knowledge base (with dedup)

    Confidence scoring:
    - High (>0.8): auto-accepted
    - Medium (0.5-0.8): stored as "suggested", needs review
    - Low (<0.5): discarded
    """

    id: UUID
    job_id: UUID
    kind: str  # "decision" | "bug" | "preference"
    confidence: float
    status: str = "suggested"  # suggested | accepted | rejected | duplicate
    data: dict = None
    source_commit: str = ""
    source_file: str = ""
    dedup_key: str = ""
    reviewed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.data is None:
            self.data = {}

    @property
    def is_auto_acceptable(self) -> bool:
        """Check if candidate should be auto-accepted."""
        return self.confidence >= 0.8

    @property
    def is_reviewable(self) -> bool:
        """Check if candidate needs human review."""
        return 0.5 <= self.confidence < 0.8

    @property
    def is_discardable(self) -> bool:
        """Check if candidate should be discarded."""
        return self.confidence < 0.5

    def accept(self) -> None:
        """Accept this candidate into the knowledge base."""
        self.status = "accepted"
        self.reviewed_at = datetime.now(timezone.utc)

    def reject(self) -> None:
        """Reject this candidate."""
        self.status = "rejected"
        self.reviewed_at = datetime.now(timezone.utc)

    def mark_duplicate(self) -> None:
        """Mark as duplicate of existing knowledge."""
        self.status = "duplicate"
        self.reviewed_at = datetime.now(timezone.utc)

    @classmethod
    def create(
        cls,
        job_id: UUID,
        kind: str,
        confidence: float,
        data: dict | None = None,
        source_commit: str = "",
        source_file: str = "",
        dedup_key: str = "",
    ) -> ExtractionCandidate:
        return cls(
            id=uuid4(),
            job_id=job_id,
            kind=kind,
            confidence=confidence,
            data=data or {},
            source_commit=source_commit,
            source_file=source_file,
            dedup_key=dedup_key,
        )
