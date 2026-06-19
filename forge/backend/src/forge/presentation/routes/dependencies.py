"""Dependency routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.search.graph_adapter import InMemoryDependencyGraph
from forge.application.code.build_dependency_graph import BuildDependencyGraphUseCase, BuildDependencyGraphRequest
from forge.application.code.get_import_graph import GetImportGraphUseCase
from forge.application.code.get_call_graph import GetCallGraphUseCase
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.dependency_schemas import (
    BuildDependencyGraphRequest as BuildSchema,
    BuildDependencyGraphResponse,
    GetImportGraphResponse,
    GetCallGraphResponse,
)

router = APIRouter(prefix="/dependencies", tags=["dependencies"])

graph_adapter = InMemoryDependencyGraph()


@router.post("/build", response_model=BuildDependencyGraphResponse, status_code=201)
async def build_dependency_graph(
    body: BuildSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    use_case = BuildDependencyGraphUseCase(graph_adapter)
    result = await use_case.execute(
        BuildDependencyGraphRequest(
            project_id=body.project_id,
            indexed_files=body.indexed_files,
        )
    )
    return BuildDependencyGraphResponse(**result.__dict__)


@router.get("/import-graph/{project_id}", response_model=GetImportGraphResponse)
async def get_import_graph(
    project_id: str,
    file_path: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    use_case = GetImportGraphUseCase(graph_adapter)
    result = await use_case.execute(project_id=project_id, file_path=file_path)
    return GetImportGraphResponse(**result.__dict__)


@router.get("/call-graph/{project_id}", response_model=GetCallGraphResponse)
async def get_call_graph(
    project_id: str,
    entry_name: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    use_case = GetCallGraphUseCase(graph_adapter)
    result = await use_case.execute(project_id=project_id, entry_name=entry_name)
    return GetCallGraphResponse(**result.__dict__)
