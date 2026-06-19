"""ChangeEntry — a single file change within a PR."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.analysis.value_objects.change_type import ChangeType


@dataclass
class ChangeEntry:
    """Represents one file changed in a pull request."""

    file_path: str
    change_type: ChangeType
    lines_added: int = 0
    lines_removed: int = 0
    is_test_file: bool = False
    is_core_module: bool = False
    language: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def net_lines(self) -> int:
        """Net line change (positive = growth)."""
        return self.lines_added - self.lines_removed

    @property
    def module_path(self) -> str:
        """Extract the module path from the file path.

        e.g. 'backend/src/forge/domain/projects/entities/project.py'
              -> 'forge.domain.projects'
        """
        parts = self.file_path.replace("\\", "/").split("/")
        # Find the 'forge' package root
        for i, part in enumerate(parts):
            if part == "forge" and i + 2 < len(parts):
                return ".".join(parts[i : i + 3])
        # Fallback: first 3 meaningful path segments
        meaningful = [p for p in parts if p not in ("src", "backend", "tests", "")]
        if len(meaningful) >= 3:
            return ".".join(meaningful[:3])
        return ".".join(meaningful) if meaningful else self.file_path
