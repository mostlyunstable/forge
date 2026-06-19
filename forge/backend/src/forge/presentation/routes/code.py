"""Code routes."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.repositories.code_repository import CodeRepository
from forge.infrastructure.code_indexer.tree_sitter_code_indexer import TreeSitterCodeIndexer
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.code.search_code import SearchCodeUseCase
from forge.application.code.get_file_entries import GetFileEntriesUseCase
from forge.application.code.index_repository import IndexRepositoryUseCase, IndexRepositoryRequest
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.code_schemas import (
    SearchCodeResponse,
    GetFileEntriesResponse,
    IndexRepositoryRequest as IndexSchema,
    IndexRepositoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code", tags=["code"])


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
