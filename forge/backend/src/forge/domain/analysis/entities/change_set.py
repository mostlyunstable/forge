"""ChangeSet — the complete set of file changes in a PR."""
from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.analysis.entities.change_entry import ChangeEntry
from forge.domain.analysis.value_objects.change_type import ChangeType


@dataclass
class ChangeSet:
    """Aggregates all file changes for a pull request."""

    entries: list[ChangeEntry] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.entries)

    @property
    def total_added(self) -> int:
        return sum(e.lines_added for e in self.entries)

    @property
    def total_removed(self) -> int:
        return sum(e.lines_removed for e in self.entries)

    @property
    def added_files(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.ADDED]

    @property
    def modified_files(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.MODIFIED]

    @property
    def deleted_files(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.DELETED]

    @property
    def test_files(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.is_test_file]

    @property
    def core_module_files(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.is_core_module]

    @property
    def unique_modules(self) -> list[str]:
        """Distinct module paths touched."""
        seen: set[str] = set()
        result: list[str] = []
        for entry in self.entries:
            mod = entry.module_path
            if mod not in seen:
                seen.add(mod)
                result.append(mod)
        return result

    @property
    def has_domain_changes(self) -> bool:
        return any("domain" in e.file_path for e in self.entries)

    @property
    def has_infrastructure_changes(self) -> bool:
        return any("infrastructure" in e.file_path for e in self.entries)

    @property
    def has_api_changes(self) -> bool:
        return any(
            "routes" in e.file_path or "schemas" in e.file_path for e in self.entries
        )

    @property
    def has_migration_changes(self) -> bool:
        return any("alembic" in e.file_path or "migration" in e.file_path for e in self.entries)
