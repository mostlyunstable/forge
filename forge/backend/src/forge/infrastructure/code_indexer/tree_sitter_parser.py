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
        file_name = Path(file_path).name
        ext = Path(file_path).suffix.lower()
        
        lookup_key = ext if ext else file_name
        if lookup_key not in LANGUAGES and file_name not in LANGUAGES:
            return self._naive_chunk_fallback(file_path, content)

        lang_key = file_name if file_name in LANGUAGES else lookup_key
        lang_name, _ = LANGUAGES[lang_key]
        parser = self._parsers.get(lang_key)
        if parser is None:
            return self._naive_chunk_fallback(file_path, content)

        try:
            tree = parser.parse(bytes(content, "utf8"))
            entries: list[ParsedEntry] = []
            self._walk(tree.root_node, content, file_path, lang_name, entries)
            
            # Deduplicate: if an entry contains other entries, replace children text with stubs
            for parent in entries:
                children = [c for c in entries if c != parent and c.start_line >= parent.start_line and c.end_line <= parent.end_line]
                if children:
                    children.sort(key=lambda x: x.start_line, reverse=True)
                    lines = parent.content.split('\n')
                    parent_start = parent.start_line
                    for child in children:
                        start_idx = child.start_line - parent_start
                        end_idx = child.end_line - parent_start + 1
                        if start_idx >= 0 and end_idx <= len(lines):
                            lines[start_idx:end_idx] = [f"    # {child.entry_type.value} {child.name} extracted..."]
                    parent.content = '\n'.join(lines)

            # Module level fallback for unextracted lines
            covered_lines = set()
            for e in entries:
                covered_lines.update(range(e.start_line, e.end_line + 1))
            
            all_lines = content.split('\n')
            uncovered_blocks = []
            current_block = []
            current_start = -1
            
            for i, line in enumerate(all_lines, 1):
                if i not in covered_lines:
                    if not current_block:
                        current_start = i
                    current_block.append(line)
                else:
                    if current_block:
                        if any(c.strip() for c in current_block):
                            uncovered_blocks.append((current_start, i - 1, '\n'.join(current_block)))
                        current_block = []
            
            if current_block and any(c.strip() for c in current_block):
                uncovered_blocks.append((current_start, len(all_lines), '\n'.join(current_block)))
                
            for start, end, text in uncovered_blocks:
                entries.append(ParsedEntry(
                    entry_type=EntryType.MODULE,
                    name=f"module_level_{start}_{end}",
                    content=text,
                    file_path=file_path,
                    language=lang_name,
                    start_line=start,
                    end_line=end,
                    metadata={}
                ))
            
            return entries
        except Exception:
            return self._naive_chunk_fallback(file_path, content)

    def _naive_chunk_fallback(self, file_path: str, content: str) -> list[ParsedEntry]:
        lines = content.split('\n')
        entries = []
        chunk_size = 100
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            if not any(c.strip() for c in chunk_lines):
                continue
            entries.append(ParsedEntry(
                entry_type=EntryType.MODULE,
                name=f"chunk_{i + 1}_{i + len(chunk_lines)}",
                content='\n'.join(chunk_lines),
                file_path=file_path,
                language="unknown",
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                metadata={}
            ))
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
        parent_name: str = "",
    ) -> None:
        entry = self._try_extract(node, content, file_path, language, parent_name)
        if entry:
            entries.append(entry)
            # Update parent_name for children of this node
            if entry.entry_type in (EntryType.CLASS, EntryType.INTERFACE):
                parent_name = entry.name

        for child in node.children:
            self._walk(child, content, file_path, language, entries, parent_name)

    def _try_extract(
        self,
        node: Any,
        content: str,
        file_path: str,
        language: str,
        parent_name: str = "",
    ) -> ParsedEntry | None:
        content_bytes = content.encode("utf8")
        node_type = node.type

        # If this node is the inner definition of a decorated_definition, skip it 
        # here because it will be extracted by the parent decorated_definition.
        if getattr(node, "parent", None) and node.parent.type == "decorated_definition":
            if node_type in ("class_definition", "function_definition", "function", "arrow_function"):
                return None

        if node_type == "decorated_definition":
            for child in node.children:
                if child.type == "class_definition":
                    entry = self._extract_class(child, content_bytes, file_path, language)
                    if entry:
                        entry.content = content_bytes[node.start_byte:node.end_byte].decode("utf8")
                        entry.start_line = node.start_point[0] + 1
                        entry.end_line = node.end_point[0] + 1
                        return entry
                elif child.type in ("function_definition", "arrow_function", "function"):
                    entry = self._extract_function(child, content_bytes, file_path, language, parent_name)
                    if entry:
                        entry.content = content_bytes[node.start_byte:node.end_byte].decode("utf8")
                        entry.start_line = node.start_point[0] + 1
                        entry.end_line = node.end_point[0] + 1
                        return entry
            return None

        if node_type == "class_definition":
            return self._extract_class(node, content_bytes, file_path, language)
        if node_type in ("function_definition", "arrow_function", "function"):
            return self._extract_function(node, content_bytes, file_path, language, parent_name)
        if node_type == "interface_declaration":
            return self._extract_interface(node, content_bytes, file_path, language)
        if node_type == "enum_declaration":
            return self._extract_enum(node, content_bytes, file_path, language)
        
        # New chunk types
        if node_type == "statement": # Typical for SQL
            return self._extract_sql_statement(node, content_bytes, file_path, language)
        if node_type in ("section", "atx_heading"): # Typical for Markdown
            return self._extract_markdown_section(node, content_bytes, file_path, language)

        return None

    def _get_name(self, node: Any, content_bytes: bytes) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node:
            return content_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
        return None

    def _extract_class(self, node: Any, content_bytes: bytes, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content_bytes)
        if not name:
            name = f"<anonymous_class_{node.start_point[0] + 1}>"
        return ParsedEntry(
            entry_type=EntryType.CLASS,
            name=name,
            content=content_bytes[node.start_byte:node.end_byte].decode("utf8"),
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_function(self, node: Any, content_bytes: bytes, file_path: str, language: str, parent_name: str = "") -> ParsedEntry | None:
        name = self._get_name(node, content_bytes)
        if not name:
            name = f"<anonymous_func_{node.start_point[0] + 1}>"
            
        if parent_name:
            name = f"{parent_name}.{name}"
            
        return ParsedEntry(
            entry_type=EntryType.FUNCTION,
            name=name,
            content=content_bytes[node.start_byte:node.end_byte].decode("utf8"),
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={"is_async": any(c.type == "async" for c in node.children)},
        )

    def _extract_interface(self, node: Any, content_bytes: bytes, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content_bytes)
        if not name:
            return None
        return ParsedEntry(
            entry_type=EntryType.INTERFACE,
            name=name,
            content=content_bytes[node.start_byte:node.end_byte].decode("utf8"),
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_enum(self, node: Any, content_bytes: bytes, file_path: str, language: str) -> ParsedEntry | None:
        name = self._get_name(node, content_bytes)
        if not name:
            return None
        return ParsedEntry(
            entry_type=EntryType.ENUM,
            name=name,
            content=content_bytes[node.start_byte:node.end_byte].decode("utf8"),
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_sql_statement(self, node: Any, content_bytes: bytes, file_path: str, language: str) -> ParsedEntry | None:
        if language != "sql":
            return None
        
        # Limit SQL statement names
        statement_content = content_bytes[node.start_byte:node.end_byte].decode("utf8")
        name = "SQL Statement"
        
        return ParsedEntry(
            entry_type=EntryType.SQL_STATEMENT,
            name=name,
            content=statement_content,
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )

    def _extract_markdown_section(self, node: Any, content_bytes: bytes, file_path: str, language: str) -> ParsedEntry | None:
        if language != "markdown":
            return None
            
        section_content = content_bytes[node.start_byte:node.end_byte].decode("utf8")
        name = "Markdown Section"
        
        # If it's a heading, we might try to extract the text
        if node.type == "atx_heading":
            # Extract header text if possible
            for child in node.children:
                if child.type == "inline":
                    name = content_bytes[child.start_byte:child.end_byte].decode("utf8").strip()
                    break

        return ParsedEntry(
            entry_type=EntryType.MARKDOWN_SECTION,
            name=name,
            content=section_content,
            file_path=file_path,
            language=language,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            metadata={},
        )
