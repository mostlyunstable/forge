"""Project routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.projects.create_project import CreateProjectUseCase, CreateProjectRequest
from forge.application.projects.get_project import GetProjectUseCase
from forge.application.projects.list_projects import ListProjectsUseCase
from forge.application.projects.update_project import UpdateProjectUseCase, UpdateProjectRequest
from forge.application.projects.delete_project import DeleteProjectUseCase
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.project_schemas import (
    CreateProjectRequest as CreateProjectSchema,
    UpdateProjectRequest as UpdateProjectSchema,
    ProjectResponse,
    ListProjectsResponse,
    DeleteResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: CreateProjectSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = ProjectRepository(session)
    use_case = CreateProjectUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(
        CreateProjectRequest(
            name=body.name,
            description=body.description,
            stack=body.stack,
            goals=body.goals,
            repository_url=body.repository_url,
        )
    )
    return ProjectResponse(**result.__dict__)


@router.get("", response_model=ListProjectsResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    skip = max(0, skip)
    limit = max(1, min(1000, limit))
    repo = ProjectRepository(session)
    use_case = ListProjectsUseCase(repo)
    result = await use_case.execute(skip=skip, limit=limit)
    return ListProjectsResponse(**result.__dict__)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = ProjectRepository(session)
    use_case = GetProjectUseCase(repo)
    result = await use_case.execute(project_id)
    return ProjectResponse(**result.__dict__)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: UpdateProjectSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = ProjectRepository(session)
    use_case = UpdateProjectUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(
        UpdateProjectRequest(
            project_id=project_id,
            description=body.description,
            stack=body.stack,
            goals=body.goals,
            repository_url=body.repository_url,
        )
    )
    return ProjectResponse(**result.__dict__)


@router.delete("/{project_id}", response_model=DeleteResponse)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = ProjectRepository(session)
    use_case = DeleteProjectUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(project_id)
    return DeleteResponse(**result.__dict__)
