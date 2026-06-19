"""Tree-sitter code indexer adapter — bridges use case port to parser infrastructure."""
from __future__ import annotations

import logging
from typing import Any

from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser
from forge.infrastructure.search.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TreeSitterCodeIndexer:
    """Adapter that implements ICodeIndexer using TreeSitterParser."""

    def __init__(self, vector_store: Any = None) -> None:
        self._parser = TreeSitterParser()
        self._embedding_service = EmbeddingService()
        self._vector_store = vector_store

    async def index(self, project_id, repo_path: str):
        import os
        from forge.domain.code.entities.code_entry import CodeEntry

        entries = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "venv", "__pycache__", "dist", "build"]]
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    parsed = self._parser.parse_file(file_path, content)
                    for p in parsed:
                        entry = CodeEntry.create(
                            project_id=project_id,
                            file_path=relative_path,
                            entry_type=p.parsed_entry_type if hasattr(p, "parsed_entry_type") else p.entry_type,
                            name=p.name,
                            content=p.content,
                            language=p.language,
                            start_line=p.start_line,
                            end_line=p.end_line,
                            metadata=p.metadata,
                        )
                        embedding_text = f"{p.name} {p.entry_type.value} {p.content[:500]}"
                        embedding = await self._embedding_service.get_embedding(embedding_text)
                        await self._vector_store.upsert_code(
                            project_id=project_id.value,
                            file_path=relative_path,
                            entry_type=p.entry_type.value,
                            name=p.name,
                            content=p.content,
                            embedding=embedding,
                            metadata=p.metadata,
                        )
                        entries.append(entry)
                except Exception as e:
                    logger.warning("Failed to index file %s: %s", file_path, e)
                    continue
        return entries
