"""TreeSitterParser - parses source code using Tree-sitter."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tree_sitter import Parser

from forge.domain.code.value_objects.entry_type import EntryType
from forge.infrastructure.code_indexer.types import ParsedEntry, ParsedDependency, LANGUAGES
from forge.infrastructure.code_indexer.dependency_extractor import DependencyExtractor


class TreeSitterParser:
    """Parses source files and extracts structured code entries."""

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}
        for lang_name, (_, language) in LANGUAGES.items():
            self._parsers[lang_name] = Parser(language)
        self._dependency_extractor = DependencyExtractor(self._parsers)

    def parse_file(self, file_path: str, content: str) -> list[ParsedEntry]:
        ext = Path(file_path).suffix.lower()
        if ext not in LANGUAGES:
            return []

        lang_name, _ = LANGUAGES[ext]
        parser = self._parsers.get(ext)
        if parser is None:
            return []

        tree = parser.parse(bytes(content, "utf8"))
        entries: list[ParsedEntry] = []
        self._walk(tree.root_node, content, file_path, lang_name, entries)
        return entries

    def extract_dependencies(self, file_path: str, content: str) -> list[ParsedDependency]:
        return self._dependency_extractor.extract(file_path, content)

    def _walk(
        self,
        node: Any,
        content: str,
        file_path: str,
        language: str,
        entries: list[ParsedEntry],
    ) -> None:
        entry = self._try_extract(node, content, file_path, language)
        if entry:
            entries.append(entry)

        for child in node.children:
            self._walk(child, content, file_path, language, entries)

    def _try_extract(
        self,
        node: Any,
        content: str,
        file_path: str,
        language: str,
    ) -> ParsedEntry | None:
        node_type = node.type

        if node_type == "class_definition":
            return self._extract_class(node, content, file_path, language)
        if node_type in ("function_definition", "arrow_function", "function"):
            return self._extract_function(node, content, file_path, language)
        if node_type == "interface_declaration":
            return self._extract_interface(node, content, file_path, language)
        if node_type == "enum_declaration":
            return self._extract_enum(node, content, file_path, language)
        return None

    def _get_name(self, node: Any, content: str) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node:
            return content[name_node.start_byte:name_node.end_byte]
        return None

    def _extract_class(self, node: Any, content: str, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content)
        if not name:
            return None
        return ParsedEntry(
            entry_type=EntryType.CLASS,
            name=name,
            content=content[node.start_byte:node.end_byte],
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_function(self, node: Any, content: str, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content)
        if not name:
            name = "<anonymous>"
        return ParsedEntry(
            entry_type=EntryType.FUNCTION,
            name=name,
            content=content[node.start_byte:node.end_byte],
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={"is_async": any(c.type == "async" for c in node.children)},
        )

    def _extract_interface(self, node: Any, content: str, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content)
        if not name:
            return None
        return ParsedEntry(
            entry_type=EntryType.INTERFACE,
            name=name,
            content=content[node.start_byte:node.end_byte],
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_enum(self, node: Any, content: str, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content)
        if not name:
            return None
        return ParsedEntry(
            entry_type=EntryType.ENUM,
            name=name,
            content=content[node.start_byte:node.end_byte],
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )
