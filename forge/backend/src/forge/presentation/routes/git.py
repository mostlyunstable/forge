"""Git routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.application.git.analyze_commits import AnalyzeCommitsUseCase
from forge.infrastructure.repositories.commit_repository import CommitRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.git_schemas import AnalyzeCommitsResponse

router = APIRouter(prefix="/git", tags=["git"])


@router.get("/commits/{project_id}", response_model=AnalyzeCommitsResponse)
async def analyze_commits(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    commit_repo = CommitRepository(session)
    project_repo = ProjectRepository(session)
    use_case = AnalyzeCommitsUseCase(commit_repo, project_repo)
    result = await use_case.execute(project_id=project_id, limit=limit)
    return AnalyzeCommitsResponse(**result.__dict__)
