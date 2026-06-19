"""Commit entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.git.value_objects.commit_classification import CommitClassification
from forge.domain.git.value_objects.commit_sha import CommitSha
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class Commit:
    """A git commit analyzed and classified by Forge."""

    project_id: ProjectId
    sha: CommitSha
    message: str
    author: str
    timestamp: datetime
    files_changed: list[str] = field(default_factory=list)
    classification: CommitClassification = CommitClassification.OTHER
    summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        sha: str,
        message: str,
        author: str,
        timestamp: datetime,
        files_changed: list[str] | None = None,
        classification: CommitClassification = CommitClassification.OTHER,
        summary: str = "",
    ) -> Commit:
        return cls(
            project_id=project_id,
            sha=CommitSha(sha),
            message=message,
            author=author,
            timestamp=timestamp,
            files_changed=files_changed or [],
            classification=classification,
            summary=summary,
        )
