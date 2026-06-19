"""Memory domain events (decisions, bugs, preferences)."""
from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class DecisionRecorded(DomainEvent):
    """Published when an architecture decision is recorded."""

    decision_id: str = ""
    project_id: str = ""
    title: str = ""

    @property
    def event_type(self) -> str:
        return "decision.recorded"

    def to_dict(self):
        base = super().to_dict()
        base["decision_id"] = self.decision_id
        base["project_id"] = self.project_id
        base["title"] = self.title
        return base


@dataclass(frozen=True)
class DecisionDeleted(DomainEvent):
    """Published when a decision is deleted."""

    decision_id: str = ""
    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "decision.deleted"

    def to_dict(self):
        base = super().to_dict()
        base["decision_id"] = self.decision_id
        base["project_id"] = self.project_id
        return base


@dataclass(frozen=True)
class BugRecorded(DomainEvent):
    """Published when a bug is recorded."""

    bug_id: str = ""
    project_id: str = ""
    title: str = ""

    @property
    def event_type(self) -> str:
        return "bug.recorded"

    def to_dict(self):
        base = super().to_dict()
        base["bug_id"] = self.bug_id
        base["project_id"] = self.project_id
        base["title"] = self.title
        return base


@dataclass(frozen=True)
class BugResolved(DomainEvent):
    """Published when a bug is marked as resolved."""

    bug_id: str = ""
    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "bug.resolved"

    def to_dict(self):
        base = super().to_dict()
        base["bug_id"] = self.bug_id
        base["project_id"] = self.project_id
        return base


@dataclass(frozen=True)
class BugReopened(DomainEvent):
    """Published when a resolved bug is reopened."""

    bug_id: str = ""
    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "bug.reopened"

    def to_dict(self):
        base = super().to_dict()
        base["bug_id"] = self.bug_id
        base["project_id"] = self.project_id
        return base


@dataclass(frozen=True)
class BugDeleted(DomainEvent):
    """Published when a bug is deleted."""

    bug_id: str = ""
    project_id: str = ""

    @property
    def event_type(self) -> str:
        return "bug.deleted"

    def to_dict(self):
        base = super().to_dict()
        base["bug_id"] = self.bug_id
        base["project_id"] = self.project_id
        return base


@dataclass(frozen=True)
class PreferenceRecorded(DomainEvent):
    """Published when a developer preference is first recorded."""

    preference_key: str = ""
    value: str = ""

    @property
    def event_type(self) -> str:
        return "preference.recorded"

    def to_dict(self):
        base = super().to_dict()
        base["preference_key"] = self.preference_key
        base["value"] = self.value
        return base


@dataclass(frozen=True)
class PreferenceStrengthened(DomainEvent):
    """Published when an existing preference's confidence is increased."""

    preference_key: str = ""
    new_confidence: float = 0.0
    evidence_count: int = 0

    @property
    def event_type(self) -> str:
        return "preference.strengthened"

    def to_dict(self):
        base = super().to_dict()
        base["preference_key"] = self.preference_key
        base["new_confidence"] = self.new_confidence
        base["evidence_count"] = self.evidence_count
        return base


@dataclass(frozen=True)
class PreferenceDeleted(DomainEvent):
    """Published when a preference is deleted."""

    preference_key: str = ""

    @property
    def event_type(self) -> str:
        return "preference.deleted"

    def to_dict(self):
        base = super().to_dict()
        base["preference_key"] = self.preference_key
        return base
