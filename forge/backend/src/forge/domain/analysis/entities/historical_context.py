"""HistoricalContext — related decisions, bugs, commits, and preferences."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RelatedDecision:
    """A historical decision relevant to the changes."""

    id: str
    title: str
    decision: str
    status: str
    relevance_reason: str = ""


@dataclass
class RelatedBug:
    """A historical bug relevant to the changes."""

    id: str
    title: str
    root_cause: str
    solution: str
    severity: str
    resolved: bool
    relevance_reason: str = ""


@dataclass
class RelatedCommit:
    """A historical commit relevant to the changes."""

    sha: str
    message: str
    classification: str
    timestamp: str
    relevance_reason: str = ""


@dataclass
class RelatedPreference:
    """A developer preference relevant to the changes."""

    key: str
    value: str
    confidence: float
    relevance_reason: str = ""


@dataclass
class HistoricalContext:
    """Aggregates all historical knowledge related to the PR changes."""

    related_decisions: list[RelatedDecision] = field(default_factory=list)
    related_bugs: list[RelatedBug] = field(default_factory=list)
    related_commits: list[RelatedCommit] = field(default_factory=list)
    related_preferences: list[RelatedPreference] = field(default_factory=list)

    @property
    def total_related_items(self) -> int:
        return (
            len(self.related_decisions)
            + len(self.related_bugs)
            + len(self.related_commits)
            + len(self.related_preferences)
        )

    @property
    def has_related_bugs(self) -> bool:
        return len(self.related_bugs) > 0

    @property
    def has_related_decisions(self) -> bool:
        return len(self.related_decisions) > 0

    @property
    def unresolved_bugs_count(self) -> int:
        return sum(1 for b in self.related_bugs if not b.resolved)
