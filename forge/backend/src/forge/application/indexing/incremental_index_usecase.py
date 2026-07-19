"""IncrementalIndexUseCase — indexes new changes since last job."""
from __future__ import annotations

import hashlib
import structlog
import os
from uuid import UUID

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

logger = structlog.get_logger()

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", "egg-info",
}


class IncrementalIndexUseCase:
    """Index new changes since last successful job. Resumable."""

    def __init__(
        self,
        job_repo: IIndexJobRepository,
        file_index_repo: IFileIndexRepository,
        candidate_repo: IExtractionCandidateRepository,
        memory_extractor: MemoryExtractor,
        git_diff_provider: IGitDiffProvider,
        commit_parser: IGitCommitParser,
        vector_store=None,
        embedding_service=None,
        dep_graph=None,
    ) -> None:
        self._job_repo = job_repo
        self._file_index_repo = file_index_repo
        self._candidate_repo = candidate_repo
        self._memory_extractor = memory_extractor
        self._git_diff_provider = git_diff_provider
        self._commit_parser = commit_parser
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._dep_graph = dep_graph
        self._code_indexer = None

    def set_code_indexer(self, indexer):
        self._code_indexer = indexer

    async def execute(
        self,
        project_id: UUID,
        repo_path: str,
        created_by: str = "api",
    ) -> IndexJob:
        """Run incremental indexing.

        Only processes:
        - New commits since last successful job
        - Files changed in those commits
        - New knowledge from those commits
        """
        # Get last successful job
        last_job = await self._job_repo.get_latest_completed(project_id)
        last_commit = None
        if last_job and last_job.checkpoint:
            last_commit = last_job.checkpoint.get("last_commit_sha")

        job = IndexJob.create(
            project_id=project_id,
            type=IndexType.INCREMENTAL,
            created_by=created_by,
        )
        job.save_checkpoint({"last_commit_sha": last_commit or ""})
        await self._job_repo.save(job)

        try:
            job.start()
            await self._job_repo.save(job)

            # Phase 1: Get changed files since last commit
            job.update_progress("detect_changes", 0, 0)
            await self._job_repo.save(job)

            if last_commit:
                changed_files = self._git_diff_provider.get_changed_files(
                    repo_path, last_commit
                )
            else:
                # No previous commit — full index needed
                job.fail("No previous commit found, use full index", "detect_changes")
                await self._job_repo.save(job)
                return job

            # Phase 2: Parse changed files
            job.update_progress("parse", 0, len(changed_files))
            await self._job_repo.save(job)

            candidates = []
            files_to_index = []
            for i, file_info in enumerate(changed_files):
                file_path = file_info["file_path"]
                change_type = file_info["change_type"]

                job.update_progress("parse", i, len(changed_files))
                if i % 10 == 0:
                    await self._job_repo.save(job)

                if change_type == "deleted":
                    # Remove file index
                    existing = await self._file_index_repo.get_by_project_and_path(
                        project_id, file_path
                    )
                    if existing:
                        await self._file_index_repo.delete_by_project(project_id)
                    # Also delete from vector store if supported
                    if self._vector_store and hasattr(self._vector_store, "delete_by_file"):
                        await self._vector_store.delete_by_file(str(project_id), file_path)
                    
                    if self._dep_graph and hasattr(self._dep_graph, "delete_file_edges"):
                        await self._dep_graph.delete_file_edges(project_id, file_path)
                    continue

                # Parse file and create/update index
                full_path = os.path.join(repo_path, file_path)
                try:
                    if not os.path.exists(full_path):
                        continue
                        
                    # Check file size (>10MB)
                    size = os.path.getsize(full_path)
                    if size > 10 * 1024 * 1024:
                        logger.warning("skipping_large_file", file=file_path, size=size, reason="too_large")
                        continue
                        
                    # Check for null bytes (binary heuristic)
                    with open(full_path, "rb") as f:
                        chunk = f.read(1024)
                        if b'\x00' in chunk:
                            logger.warning("skipping_binary_file", file=file_path, reason="binary")
                            continue

                    with open(full_path, "rb") as f:
                        content_hash = hashlib.sha256(f.read()).hexdigest()[:16]

                    # Check if file actually changed
                    existing = await self._file_index_repo.get_by_project_and_path(
                        project_id, file_path
                    )
                    if existing and not existing.needs_reindex(content_hash):
                        continue

                    # Create or update file index
                    language = self._detect_language(file_path)
                    file_index = FileIndex.create(
                        project_id=project_id,
                        file_path=file_path,
                        content_hash=content_hash,
                        language=language,
                        last_indexed_commit=job.checkpoint.get("last_commit_sha", ""),
                        index_job_id=job.id,
                    )
                    if existing:
                        file_index.id = existing.id
                        if self._vector_store and hasattr(self._vector_store, "delete_by_file"):
                            await self._vector_store.delete_by_file(str(project_id), file_path)
                        if self._dep_graph and hasattr(self._dep_graph, "delete_file_edges"):
                            await self._dep_graph.delete_file_edges(project_id, file_path)
                    await self._file_index_repo.save(file_index)
                    files_to_index.append(file_path)

                    # Extract code comments
                    ext = os.path.splitext(file_path)[1]
                    if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs"}:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            
                        if self._dep_graph and hasattr(self._dep_graph, "add_file_edges"):
                            await self._dep_graph.add_file_edges(project_id, file_path, content)
                            
                        code_candidates = self._memory_extractor.extract_from_code_comments(
                            job_id=job.id,
                            file_path=file_path,
                            content=content,
                        )
                        candidates.extend(code_candidates)

                except Exception as e:
                    job.log_error(file_path, str(e), "parse")

            if self._code_indexer and files_to_index:
                logger.info("re-indexing_changed_files", count=len(files_to_index))
                await self._code_indexer.index_files(project_id, repo_path, files_to_index, self._commit_parser)

            # Phase 3: Extract knowledge from new commits
            job.update_progress("extract", 0, 0)
            await self._job_repo.save(job)

            commits = self._commit_parser.get_commit_history(
                repo_path, since=last_commit, limit=500
            )
            for commit in commits:
                commit_candidates = self._memory_extractor.extract_from_commit_message(
                    job_id=job.id,
                    commit_sha=commit.sha,
                    message=commit.message,
                    author_name=commit.author_name,
                    files_changed=commit.files_changed,
                )
                candidates.extend(commit_candidates)

            # Save candidates
            if candidates:
                await self._candidate_repo.save_many(candidates)

            # Auto-accept high-confidence candidates
            auto_accepted = 0
            for c in candidates:
                if c.is_auto_acceptable:
                    c.accept()
                    await self._candidate_repo.save(c)
                    auto_accepted += 1

            # Complete job
            latest_commit = self._git_diff_provider.get_latest_commit(repo_path)
            result = {
                "files_changed": len(changed_files),
                "candidates_extracted": len(candidates),
                "auto_accepted": auto_accepted,
                "commits_processed": len(commits),
            }
            job.save_checkpoint({"last_commit_sha": latest_commit or ""})
            state_hash = self._compute_state_hash(project_id, latest_commit)
            job.complete(result, state_hash)
            await self._job_repo.save(job)

            logger.info(
                "incremental_index_completed",
                project_id=str(project_id),
                files_changed=len(changed_files),
                candidates=len(candidates),
            )

            return job

        except Exception as e:
            job.fail(str(e), "incremental_index")
            await self._job_repo.save(job)
            logger.error("incremental_index_failed", error=str(e))
            raise

    def _detect_language(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "jsx", ".go": "go", ".rs": "rust",
            ".java": "java", ".rb": "ruby", ".c": "c", ".cpp": "cpp",
        }
        return language_map.get(ext, "")

    def _compute_state_hash(self, project_id: UUID, latest_commit: str | None) -> str:
        content = f"{project_id}:{latest_commit or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
