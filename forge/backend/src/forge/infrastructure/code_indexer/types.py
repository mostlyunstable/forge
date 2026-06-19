"""Shared types for code parsing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import tree_sitter_python as tspython
import tree_sitter_typescript as ts_typescript
import tree_sitter_javascript as tsjs
from tree_sitter import Language

from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.code.value_objects.dependency_type import DependencyType


LANGUAGES = {
    ".py": ("python", Language(tspython.language())),
    ".ts": ("typescript", Language(ts_typescript.language_typescript())),
    ".tsx": ("tsx", Language(ts_typescript.language_tsx())),
    ".js": ("javascript", Language(tsjs.language())),
    ".jsx": ("jsx", Language(tsjs.language())),
}


@dataclass
class ParsedEntry:
    """Intermediate representation of a parsed code entry."""

    entry_type: EntryType
    name: str
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    metadata: dict[str, Any]


@dataclass
class ParsedDependency:
    """Intermediate representation of a parsed dependency."""

    dependency_type: DependencyType
    source_file: str
    target_module: str
    target_name: str
    line_number: int
    metadata: dict[str, Any]
