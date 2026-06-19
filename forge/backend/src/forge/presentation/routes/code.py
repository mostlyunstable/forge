"""Code routes."""
import logging
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.repositories.code_repository import CodeRepository
from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser
from forge.infrastructure.search.embedding_service import EmbeddingService
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.code.search_code import SearchCodeUseCase
from forge.application.code.get_file_entries import GetFileEntriesUseCase
from forge.application.code.index_repository import IndexRepositoryUseCase, IndexRepositoryRequest
from forge.presentation.deps import get_session, get_vector_store
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.code_schemas import (
    SearchCodeResponse,
    GetFileEntriesResponse,
    IndexRepositoryRequest as IndexSchema,
    IndexRepositoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code", tags=["code"])


class TreeSitterCodeIndexer:
    """Adapter that wraps TreeSitterParser for the use case port."""

    def __init__(self, vector_store: Any = None) -> None:
        self._parser = TreeSitterParser()
        self._embedding_service = EmbeddingService()
        self._vector_store = vector_store or get_vector_store()

    async def index(self, project_id, repo_path: str):
        import os
        from pathlib import Path
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


@router.post("/index", response_model=IndexRepositoryResponse, status_code=201)
async def index_repository(
    body: IndexSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    project_repo = ProjectRepository(session)
    code_repo = CodeRepository(session)
    code_indexer = TreeSitterCodeIndexer()
    use_case = IndexRepositoryUseCase(project_repo, code_repo, code_indexer, event_bus=event_bus)
    result = await use_case.execute(
        IndexRepositoryRequest(
            project_id=body.project_id,
            repo_path=body.repo_path,
        )
    )
    return IndexRepositoryResponse(**result.__dict__)


@router.get("/search", response_model=SearchCodeResponse)
async def search_code(
    q: str = Query(..., min_length=1),
    project_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = CodeRepository(session)
    use_case = SearchCodeUseCase(repo)
    result = await use_case.execute(query=q, project_id=project_id)
    return SearchCodeResponse(**result.__dict__)


@router.get("/files/{project_id}/{file_path:path}", response_model=GetFileEntriesResponse)
async def get_file_entries(
    project_id: str,
    file_path: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = CodeRepository(session)
    use_case = GetFileEntriesUseCase(repo)
    result = await use_case.execute(project_id=project_id, file_path=file_path)
    return GetFileEntriesResponse(**result.__dict__)
