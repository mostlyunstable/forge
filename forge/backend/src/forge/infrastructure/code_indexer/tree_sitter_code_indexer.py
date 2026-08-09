"""Tree-sitter code indexer adapter — bridges use case port to parser infrastructure."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import diskcache

from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser
from forge.infrastructure.search.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TreeSitterCodeIndexer:
    """Adapter that implements ICodeIndexer using TreeSitterParser."""

    def __init__(self, vector_store: Any = None) -> None:
        self._parser = TreeSitterParser()
        self._embedding_service = EmbeddingService()
        self._vector_store = vector_store
        self._cache = diskcache.Cache(".forge_ast_cache")

    async def index(self, project_id, repo_path: str, commit_parser: Any = None):
        import os

        from forge.domain.code.entities.code_entry import CodeEntry

        entries = []
        batch_texts: list[str] = []
        batch_payloads: list[dict[str, Any]] = []
        BATCH_SIZE = 50

        async def flush_batch():
            if not batch_texts:
                return
            try:
                # We assume embedding_service supports get_embeddings for a list
                embeddings = await self._embedding_service.get_embeddings(batch_texts)
                for payload, embedding in zip(batch_payloads, embeddings):
                    await self._vector_store.upsert_code(
                        project_id=payload["project_id"],
                        file_path=payload["file_path"],
                        entry_type=payload["entry_type"],
                        name=payload["name"],
                        content=payload["content"],
                        embedding=embedding,
                        metadata=payload["metadata"],
                    )
            except Exception as e:
                logger.warning("batch_embed_failed %s", str(e))
                # Fallback to single embedding
                for payload, text in zip(batch_payloads, batch_texts):
                    try:
                        emb = await self._embedding_service.get_embedding(text)
                        await self._vector_store.upsert_code(
                            project_id=payload["project_id"],
                            file_path=payload["file_path"],
                            entry_type=payload["entry_type"],
                            name=payload["name"],
                            content=payload["content"],
                            embedding=emb,
                            metadata=payload["metadata"],
                        )
                    except Exception as inner_e:
                        logger.warning("single_embed_failed %s", str(inner_e))
            batch_texts.clear()
            batch_payloads.clear()

        import fnmatch

        # simple gitignore
        ignore_patterns = set(
            ["node_modules", "venv", "__pycache__", "dist", "build", "coverage", "vendor", "cache"]
        )
        gitignore_path = os.path.join(os.path.realpath(repo_path), ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            ignore_patterns.add(line.rstrip("/"))
            except Exception:
                pass

        def is_ignored(path):
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(
                    os.path.basename(path), pattern
                ):
                    return True
            return False

        real_repo_path = os.path.realpath(repo_path)
        for root, dirs, files in os.walk(real_repo_path):
            real_root = os.path.realpath(root)
            if not real_root.startswith(real_repo_path):
                dirs[:] = []
                continue

            dirs[:] = [d for d in dirs if not d.startswith(".") and not is_ignored(d)]
            for file in files:
                if file.startswith(".") or is_ignored(file):
                    continue

                file_path = os.path.join(root, file)
                real_file_path = os.path.realpath(file_path)

                if not real_file_path.startswith(real_repo_path):
                    continue

                relative_path = os.path.relpath(real_file_path, real_repo_path)
                try:
                    with open(real_file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    cache_key = f"{relative_path}_{content_hash}"
                    parsed = self._cache.get(cache_key)
                    if parsed is None:
                        parsed = self._parser.parse_file(real_file_path, content)
                        self._cache.set(cache_key, parsed, expire=86400 * 7)

                    git_metadata = {}
                    if commit_parser:
                        git_metadata = commit_parser.get_file_metadata(repo_path, relative_path)

                    for p in parsed:
                        metadata = p.metadata.copy()
                        metadata.update(git_metadata)
                        metadata["repository"] = repo_path
                        metadata["start_line"] = p.start_line
                        metadata["end_line"] = p.end_line

                        entry = CodeEntry.create(
                            project_id=project_id,
                            file_path=relative_path,
                            entry_type=p.parsed_entry_type
                            if hasattr(p, "parsed_entry_type")
                            else p.entry_type,
                            name=p.name,
                            content=p.content,
                            language=p.language,
                            start_line=p.start_line,
                            end_line=p.end_line,
                            metadata=metadata,  # type: ignore
                        )
                        embedding_text = f"File: {relative_path}\n{p.name} {p.entry_type.value}\n{p.content[:1500]}"

                        batch_texts.append(embedding_text)
                        batch_payloads.append(
                            {
                                "project_id": project_id.value
                                if hasattr(project_id, "value")
                                else project_id,
                                "file_path": relative_path,
                                "entry_type": p.entry_type.value,
                                "name": p.name,
                                "content": p.content,
                                "metadata": metadata,
                            }
                        )
                        entries.append(entry)

                        if len(batch_texts) >= BATCH_SIZE:
                            await flush_batch()
                except Exception as e:
                    logger.warning("Failed to index file %s: %s", file_path, e)
                    continue

        await flush_batch()
        return entries

    async def index_files(
        self, project_id, repo_path: str, files: list[str], commit_parser: Any = None
    ):
        import os

        from forge.domain.code.entities.code_entry import CodeEntry

        entries = []
        batch_texts: list[str] = []
        batch_payloads: list[dict[str, Any]] = []
        BATCH_SIZE = 50

        async def flush_batch():
            if not batch_texts:
                return
            try:
                embeddings = await self._embedding_service.get_embeddings(batch_texts)
                for payload, embedding in zip(batch_payloads, embeddings):
                    await self._vector_store.upsert_code(
                        project_id=payload["project_id"],
                        file_path=payload["file_path"],
                        entry_type=payload["entry_type"],
                        name=payload["name"],
                        content=payload["content"],
                        embedding=embedding,
                        metadata=payload["metadata"],
                    )
            except Exception as e:
                logger.warning("batch_embed_failed %s", str(e))
                for payload, text in zip(batch_payloads, batch_texts):
                    try:
                        emb = await self._embedding_service.get_embedding(text)
                        await self._vector_store.upsert_code(
                            project_id=payload["project_id"],
                            file_path=payload["file_path"],
                            entry_type=payload["entry_type"],
                            name=payload["name"],
                            content=payload["content"],
                            embedding=emb,
                            metadata=payload["metadata"],
                        )
                    except Exception as inner_e:
                        logger.warning("single_embed_failed %s", str(inner_e))
            batch_texts.clear()
            batch_payloads.clear()

        real_repo_path = os.path.realpath(repo_path)
        for file_path in files:
            full_path = os.path.realpath(os.path.join(real_repo_path, file_path))
            if not full_path.startswith(real_repo_path):
                continue
            if not os.path.exists(full_path):
                continue
            try:
                with open(full_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                git_metadata = {}
                if commit_parser:
                    git_metadata = commit_parser.get_file_metadata(repo_path, file_path)

                parsed = self._parser.parse_file(full_path, content)
                for p in parsed:
                    metadata = p.metadata.copy()
                    metadata.update(git_metadata)
                    metadata["repository"] = repo_path
                    metadata["start_line"] = p.start_line
                    metadata["end_line"] = p.end_line

                    entry = CodeEntry.create(
                        project_id=project_id,
                        file_path=file_path,
                        entry_type=p.parsed_entry_type
                        if hasattr(p, "parsed_entry_type")
                        else p.entry_type,
                        name=p.name,
                        content=p.content,
                        language=p.language,
                        start_line=p.start_line,
                        end_line=p.end_line,
                        metadata=metadata,  # type: ignore
                    )
                    embedding_text = (
                        f"File: {file_path}\n{p.name} {p.entry_type.value}\n{p.content[:1500]}"
                    )

                    batch_texts.append(embedding_text)
                    batch_payloads.append(
                        {
                            "project_id": project_id.value
                            if hasattr(project_id, "value")
                            else project_id,
                            "file_path": file_path,
                            "entry_type": p.entry_type.value,
                            "name": p.name,
                            "content": p.content,
                            "metadata": metadata,
                        }
                    )
                    entries.append(entry)

                    if len(batch_texts) >= BATCH_SIZE:
                        await flush_batch()
            except Exception as e:
                logger.warning("Failed to index file %s: %s", file_path, e)
                continue

        await flush_batch()
        return entries
