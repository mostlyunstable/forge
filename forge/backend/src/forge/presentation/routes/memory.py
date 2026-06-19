"""Memory routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.decision_repository import DecisionRepository
from forge.infrastructure.repositories.bug_repository import BugRepository
from forge.infrastructure.repositories.preference_repository import PreferenceRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.memory.save_decision import SaveDecisionUseCase, SaveDecisionRequest
from forge.application.memory.save_bug import SaveBugUseCase, SaveBugRequest
from forge.application.memory.save_preference import SavePreferenceUseCase, SavePreferenceRequest
from forge.application.memory.get_decision import GetDecisionUseCase
from forge.application.memory.get_bug import GetBugUseCase
from forge.application.memory.list_decisions import ListDecisionsUseCase
from forge.application.memory.list_bugs import ListBugsUseCase
from forge.application.memory.update_decision import UpdateDecisionUseCase, UpdateDecisionRequest
from forge.application.memory.update_bug import UpdateBugUseCase, UpdateBugRequest
from forge.application.memory.delete_decision import DeleteDecisionUseCase
from forge.application.memory.delete_bug import DeleteBugUseCase
from forge.application.memory.delete_preference import DeletePreferenceUseCase
from forge.application.memory.search_memories import SearchMemoriesUseCase
from forge.application.memory.get_preferences import GetPreferencesUseCase
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.memory_schemas import (
    SaveDecisionRequest as DecisionSchema,
    SaveBugRequest as BugSchema,
    SavePreferenceRequest as PreferenceSchema,
    UpdateDecisionRequest as UpdateDecisionSchema,
    UpdateBugRequest as UpdateBugSchema,
    DecisionResponse,
    BugResponse,
    PreferenceResponse,
    SearchMemoriesResponse,
    GetPreferencesResponse,
    ListDecisionsResponse,
    ListBugsResponse,
    DeleteResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def save_decision(
    body: DecisionSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    decision_repo = DecisionRepository(session)
    project_repo = ProjectRepository(session)
    use_case = SaveDecisionUseCase(decision_repo, project_repo, event_bus=event_bus)
    result = await use_case.execute(
        SaveDecisionRequest(
            project_id=body.project_id,
            title=body.title,
            decision=body.decision,
            reason=body.reason,
            alternatives=body.alternatives,
        )
    )
    return DecisionResponse(**result.__dict__)


@router.get("/decisions", response_model=ListDecisionsResponse)
async def list_decisions(
    project_id: str = Query(...),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    decision_repo = DecisionRepository(session)
    project_repo = ProjectRepository(session)
    use_case = ListDecisionsUseCase(decision_repo, project_repo)
    result = await use_case.execute(project_id=project_id, skip=skip, limit=limit)
    return ListDecisionsResponse(**result.__dict__)


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = DecisionRepository(session)
    use_case = GetDecisionUseCase(repo)
    result = await use_case.execute(decision_id)
    return DecisionResponse(**result.__dict__)


@router.put("/decisions/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: str,
    body: UpdateDecisionSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = DecisionRepository(session)
    use_case = UpdateDecisionUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(
        UpdateDecisionRequest(
            decision_id=decision_id,
            title=body.title,
            decision=body.decision,
            reason=body.reason,
            alternatives=body.alternatives,
            status=body.status,
        )
    )
    return DecisionResponse(**result.__dict__)


@router.delete("/decisions/{decision_id}", response_model=DeleteResponse)
async def delete_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = DecisionRepository(session)
    use_case = DeleteDecisionUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(decision_id)
    return DeleteResponse(deleted=result.deleted, id=result.decision_id)


@router.post("/bugs", response_model=BugResponse, status_code=201)
async def save_bug(
    body: BugSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    bug_repo = BugRepository(session)
    project_repo = ProjectRepository(session)
    use_case = SaveBugUseCase(bug_repo, project_repo, event_bus=event_bus)
    result = await use_case.execute(
        SaveBugRequest(
            project_id=body.project_id,
            title=body.title,
            problem=body.problem,
            root_cause=body.root_cause,
            solution=body.solution,
            affected_files=body.affected_files,
            severity=body.severity,
        )
    )
    return BugResponse(**result.__dict__)


@router.get("/bugs", response_model=ListBugsResponse)
async def list_bugs(
    project_id: str = Query(...),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    bug_repo = BugRepository(session)
    project_repo = ProjectRepository(session)
    use_case = ListBugsUseCase(bug_repo, project_repo)
    result = await use_case.execute(project_id=project_id, skip=skip, limit=limit)
    return ListBugsResponse(**result.__dict__)


@router.get("/bugs/{bug_id}", response_model=BugResponse)
async def get_bug(
    bug_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = BugRepository(session)
    use_case = GetBugUseCase(repo)
    result = await use_case.execute(bug_id)
    return BugResponse(**result.__dict__)


@router.put("/bugs/{bug_id}", response_model=BugResponse)
async def update_bug(
    bug_id: str,
    body: UpdateBugSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = BugRepository(session)
    use_case = UpdateBugUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(
        UpdateBugRequest(
            bug_id=bug_id,
            title=body.title,
            problem=body.problem,
            root_cause=body.root_cause,
            solution=body.solution,
            affected_files=body.affected_files,
            severity=body.severity,
            resolved=body.resolved,
        )
    )
    return BugResponse(**result.__dict__)


@router.delete("/bugs/{bug_id}", response_model=DeleteResponse)
async def delete_bug(
    bug_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = BugRepository(session)
    use_case = DeleteBugUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(bug_id)
    return DeleteResponse(deleted=result.deleted, id=result.bug_id)


@router.post("/preferences", response_model=PreferenceResponse, status_code=201)
async def save_preference(
    body: PreferenceSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = PreferenceRepository(session)
    use_case = SavePreferenceUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(
        SavePreferenceRequest(
            key=body.key,
            value=body.value,
            confidence=body.confidence,
        )
    )
    return PreferenceResponse(**result.__dict__)


@router.get("/preferences", response_model=GetPreferencesResponse)
async def get_preferences(
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = PreferenceRepository(session)
    use_case = GetPreferencesUseCase(repo)
    result = await use_case.execute()
    preferences = [
        PreferenceResponse(
            key=s.key,
            value=s.value,
            confidence=s.confidence,
            evidence_count=s.evidence_count,
            created_at="",
            updated_at="",
        )
        for s in result.preferences
    ]
    return GetPreferencesResponse(preferences=preferences, total=result.total)


@router.delete("/preferences/{key}", response_model=DeleteResponse)
async def delete_preference(
    key: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    repo = PreferenceRepository(session)
    use_case = DeletePreferenceUseCase(repo, event_bus=event_bus)
    result = await use_case.execute(key)
    return DeleteResponse(deleted=result.deleted, id=result.key)


@router.get("/search", response_model=SearchMemoriesResponse)
async def search_memories(
    q: str = Query(..., min_length=1),
    project_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    decision_repo = DecisionRepository(session)
    bug_repo = BugRepository(session)
    project_repo = ProjectRepository(session)
    use_case = SearchMemoriesUseCase(decision_repo, bug_repo, project_repo)
    result = await use_case.execute(query=q, project_id=project_id)
    return SearchMemoriesResponse(**result.__dict__)
