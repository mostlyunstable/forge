"""FileIndex — tracks indexed files and their state."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class FileIndex:
    """Tracks a single file's indexing state.

    Used to detect changes and avoid re-parsing unchanged files.
    """

    id: UUID
    project_id: UUID
    file_path: str
    content_hash: str
    language: str = ""
    last_indexed_commit: str = ""
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    index_job_id: UUID | None = None

    def needs_reindex(self, current_hash: str) -> bool:
        """Check if file needs re-indexing based on content hash."""
        return self.content_hash != current_hash

    @classmethod
    def create(
        cls,
        project_id: UUID,
        file_path: str,
        content_hash: str,
        language: str = "",
        last_indexed_commit: str = "",
        index_job_id: UUID | None = None,
    ) -> FileIndex:
        return cls(
            id=uuid4(),
            project_id=project_id,
            file_path=file_path,
            content_hash=content_hash,
            language=language,
            last_indexed_commit=last_indexed_commit,
            index_job_id=index_job_id,
        )
