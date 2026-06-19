"""DependencyExtractor - extracts dependency information from parsed ASTs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.infrastructure.code_indexer.types import ParsedDependency, LANGUAGES

from tree_sitter import Language, Parser


class DependencyExtractor:
    """Extracts dependency information from source code ASTs."""

    def __init__(self, parsers: dict[str, Parser]) -> None:
        self._parsers = parsers

    def extract(
        self,
        file_path: str,
        content: str,
    ) -> list[ParsedDependency]:
        ext = Path(file_path).suffix.lower()
        if ext not in LANGUAGES:
            return []

        lang_name, _ = LANGUAGES[ext]
        parser = self._parsers.get(ext)
        if parser is None:
            return []

        tree = parser.parse(bytes(content, "utf8"))
        dependencies: list[ParsedDependency] = []
        self._walk(tree.root_node, content, file_path, lang_name, dependencies)
        return dependencies

    def _walk(
        self,
        node: Any,
        content: str,
        file_path: str,
        language: str,
        dependencies: list[ParsedDependency],
    ) -> None:
        dep = self._try_extract(node, content, file_path, language)
        if dep:
            dependencies.append(dep)

        for child in node.children:
            self._walk(child, content, file_path, language, dependencies)

    def _try_extract(
        self,
        node: Any,
        content: str,
        file_path: str,
        language: str,
    ) -> ParsedDependency | None:
        node_type = node.type

        if language == "python":
            if node_type == "import_statement":
                return self._extract_python_import(node, content, file_path)
            if node_type == "import_from_statement":
                return self._extract_python_from_import(node, content, file_path)
        elif language in ("typescript", "tsx", "javascript", "jsx"):
            if node_type == "import_statement":
                return self._extract_js_import(node, content, file_path)
            if node_type in ("class_declaration", "class"):
                return self._extract_class_extends(node, content, file_path)
        return None

    def _extract_python_import(
        self,
        node: Any,
        content: str,
        file_path: str,
    ) -> ParsedDependency | None:
        module_name = content[node.start_byte:node.end_byte]
        module_name = module_name.replace("import ", "").strip()
        return ParsedDependency(
            dependency_type=DependencyType.IMPORT,
            source_file=file_path,
            target_module=module_name,
            target_name=module_name.split(".")[-1],
            line_number=node.start_point[0] + 1,
            metadata={"raw": module_name},
        )

    def _extract_python_from_import(
        self,
        node: Any,
        content: str,
        file_path: str,
    ) -> ParsedDependency | None:
        raw = content[node.start_byte:node.end_byte]
        parts = raw.split(" import ")
        if len(parts) != 2:
            return None
        module_name = parts[0].replace("from ", "").strip()
        imported_names = [n.strip() for n in parts[1].split(",")]
        return ParsedDependency(
            dependency_type=DependencyType.FROM_IMPORT,
            source_file=file_path,
            target_module=module_name,
            target_name=",".join(imported_names),
            line_number=node.start_point[0] + 1,
            metadata={"raw": raw, "imports": imported_names},
        )

    def _extract_js_import(
        self,
        node: Any,
        content: str,
        file_path: str,
    ) -> ParsedDependency | None:
        raw = content[node.start_byte:node.end_byte]
        if "from " in raw:
            parts = raw.split(" from ")
            if len(parts) == 2:
                module_name = parts[1].strip().strip("'\"").strip(";")
                return ParsedDependency(
                    dependency_type=DependencyType.IMPORT,
                    source_file=file_path,
                    target_module=module_name,
                    target_name=module_name,
                    line_number=node.start_point[0] + 1,
                    metadata={"raw": raw},
                )
        return None

    def _extract_class_extends(
        self,
        node: Any,
        content: str,
        file_path: str,
    ) -> ParsedDependency | None:
        for child in node.children:
            if child.type == "class_heritage":
                heritage = content[child.start_byte:child.end_byte]
                if "extends" in heritage:
                    parent = heritage.split("extends")[-1].strip().split("{")[0].strip()
                    return ParsedDependency(
                        dependency_type=DependencyType.EXTENDS,
                        source_file=file_path,
                        target_module="",
                        target_name=parent,
                        line_number=node.start_point[0] + 1,
                        metadata={"parent_class": parent},
                    )
                if "implements" in heritage:
                    interfaces = heritage.split("implements")[-1].strip()
                    return ParsedDependency(
                        dependency_type=DependencyType.IMPLEMENTS,
                        source_file=file_path,
                        target_module="",
                        target_name=interfaces,
                        line_number=node.start_point[0] + 1,
                        metadata={"interfaces": interfaces},
                    )
        return None
