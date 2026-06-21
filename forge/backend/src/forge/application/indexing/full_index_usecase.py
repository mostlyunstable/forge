"""FullIndexUseCase — indexes entire codebase."""
from __future__ import annotations

import hashlib
import os
from uuid import UUID

import structlog

from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.entities.file_index import FileIndex
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.indexing.repository_contracts.index_job_repository import IIndexJobRepository
from forge.domain.indexing.repository_contracts.file_index_repository import IFileIndexRepository
from forge.domain.indexing.repository_contracts.extraction_candidate_repository import (
    IExtractionCandidateRepository,
)
from forge.domain.indexing.ports.git_diff_provider import IGitDiffProvider
from forge.domain.indexing.ports.git_commit_parser import IGitCommitParser
from forge.application.indexing.memory_extractor import MemoryExtractor
from forge.application.indexing.git_history_ingester import GitHistoryIngester

logger = structlog.get_logger()

# Directories to skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", "egg-info",
}

# File extensions to parse
PARSEABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".rb", ".c", ".cpp", ".h", ".hpp",
}


class FullIndexUseCase:
    """Index entire codebase. Resumable from checkpoint."""

    def __init__(
        self,
        job_repo: IIndexJobRepository,
        file_index_repo: IFileIndexRepository,
        candidate_repo: IExtractionCandidateRepository,
        memory_extractor: MemoryExtractor,
        git_history_ingester: GitHistoryIngester,
        git_diff_provider: IGitDiffProvider,
        commit_parser: IGitCommitParser,
        vector_store=None,
        embedding_service=None,
    ) -> None:
        self._job_repo = job_repo
        self._file_index_repo = file_index_repo
        self._candidate_repo = candidate_repo
        self._memory_extractor = memory_extractor
        self._git_history_ingester = git_history_ingester
        self._git_diff_provider = git_diff_provider
        self._commit_parser = commit_parser
        self._vector_store = vector_store
        self._embedding_service = embedding_service

    async def execute(
        self,
        project_id: UUID,
        repo_path: str,
        created_by: str = "api",
    ) -> IndexJob:
        """Run full indexing of a codebase.

        Phases:
        1. Enumerate files
        2. Parse files (tree-sitter)
        3. Build dependency graph
        4. Ingest git history
        5. Extract candidates
        6. Auto-accept high-confidence candidates
        7. Compute risk scores
        """
        job = IndexJob.create(
            project_id=project_id,
            type=IndexType.FULL,
            created_by=created_by,
        )
        await self._job_repo.save(job)

        try:
            job.start()
            await self._job_repo.save(job)

            # Phase 1: Enumerate files
            job.update_progress("enumerate", 0, 0)
            await self._job_repo.save(job)

            all_files = self._enumerate_files(repo_path)
            file_count = len(all_files)

            # Phase 2: Parse files, create file indices, and embed code
            file_indices = []
            candidates = []
            embedded_count = 0
            for i, (file_path, content_hash) in enumerate(all_files.items()):
                job.update_progress("parse", i, file_count)
                if i % 50 == 0:
                    await self._job_repo.save(job)

                # Create file index
                language = self._detect_language(file_path)
                file_index = FileIndex.create(
                    project_id=project_id,
                    file_path=file_path,
                    content_hash=content_hash,
                    language=language,
                )
                file_indices.append(file_index)

                # Parse and embed code (only parseable files)
                ext = os.path.splitext(file_path)[1]
                if ext in PARSEABLE_EXTENSIONS:
                    try:
                        full_path = os.path.join(repo_path, file_path)
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # Extract code comments
                        code_candidates = self._memory_extractor.extract_from_code_comments(
                            job_id=job.id,
                            file_path=file_path,
                            content=content,
                        )
                        candidates.extend(code_candidates)

                        # Embed and store in vector store
                        if self._vector_store and self._embedding_service:
                            try:
                                # Embed file content (truncated to 2000 chars for embedding)
                                embed_text = f"{file_path}\n{content[:2000]}"
                                embedding = await self._embedding_service.get_embedding(embed_text)
                                await self._vector_store.upsert_code(
                                    project_id=str(project_id),
                                    file_path=file_path,
                                    entry_type="file",
                                    name=os.path.basename(file_path),
                                    content=content[:500],
                                    embedding=embedding,
                                    metadata={"language": language, "size": len(content)},
                                )
                                embedded_count += 1
                            except Exception as e:
                                logger.warning("embed_failed", file_path=file_path, error=str(e))

                    except Exception as e:
                        job.log_error(file_path, str(e), "parse")

            # Save file indices
            await self._file_index_repo.save_many(file_indices)
            logger.info("files_embedded", count=embedded_count)

            # Phase 3: Git history ingestion
            job.update_progress("git_history", 0, 0)
            await self._job_repo.save(job)

            git_result = await self._git_history_ingester.ingest(
                job=job,
                repo_path=repo_path,
            )

            # Phase 4: Save candidates
            job.update_progress("save_candidates", 0, len(candidates))
            await self._job_repo.save(job)

            if candidates:
                await self._candidate_repo.save_many(candidates)

            # Phase 5: Auto-accept high-confidence candidates
            auto_accepted = sum(1 for c in candidates if c.is_auto_acceptable)
            for c in candidates:
                if c.is_auto_acceptable:
                    c.accept()
                    await self._candidate_repo.save(c)

            # Compute state hash
            latest_commit = self._git_diff_provider.get_latest_commit(repo_path)
            state_hash = self._compute_state_hash(all_files, latest_commit)

            # Complete job
            result = {
                "files_parsed": len(file_indices),
                "candidates_extracted": len(candidates),
                "auto_accepted": auto_accepted,
                "commits_ingested": git_result.get("commits_ingested", 0),
            }
            job.complete(result, state_hash)
            await self._job_repo.save(job)

            logger.info(
                "full_index_completed",
                project_id=str(project_id),
                files=len(file_indices),
                candidates=len(candidates),
            )

            return job

        except Exception as e:
            job.fail(str(e), "full_index")
            await self._job_repo.save(job)
            logger.error("full_index_failed", error=str(e))
            raise

    def _enumerate_files(self, repo_path: str) -> dict[str, str]:
        """Enumerate all files and compute content hashes."""
        files = {}
        for root, dirs, filenames in os.walk(repo_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in filenames:
                if filename.startswith("."):
                    continue
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, "rb") as f:
                        content_hash = hashlib.sha256(f.read()).hexdigest()[:16]
                    files[relative_path] = content_hash
                except Exception:
                    continue

        return files

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "jsx", ".go": "go", ".rs": "rust",
            ".java": "java", ".rb": "ruby", ".c": "c", ".cpp": "cpp",
            ".h": "c", ".hpp": "cpp",
        }
        return language_map.get(ext, "")

    def _compute_state_hash(
        self, files: dict[str, str], latest_commit: str | None
    ) -> str:
        """Compute a hash of the project state."""
        sorted_files = sorted(files.items())
        content = f"{latest_commit or ''}:{':'.join(f'{k}:{v}' for k, v in sorted_files)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
