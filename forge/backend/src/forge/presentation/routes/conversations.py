"""Conversation routes — CRUD, multi-turn messaging, search."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.search.context_retriever import ContextRetriever
from forge.infrastructure.search.in_memory_vector_store import in_memory_vector_store
from forge.infrastructure.llm.llm_service import LLMService
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.application.conversation.create_conversation import (
    CreateConversationUseCase,
    CreateConversationRequest,
)
from forge.application.conversation.send_conversation_message import (
    SendConversationMessageUseCase,
    SendMessageRequest,
)
from forge.application.conversation.get_conversation_history import GetConversationHistoryUseCase
from forge.application.conversation.list_conversations import ListConversationsUseCase
from forge.application.conversation.rename_conversation import (
    RenameConversationUseCase,
    RenameConversationRequest,
)
from forge.application.conversation.delete_conversation import DeleteConversationUseCase
from forge.application.conversation.search_conversations import SearchConversationsUseCase
from forge.application.conversation.summarize_conversation import SummarizeConversationUseCase
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.conversation_schemas import (
    CreateConversationRequest as CreateSchema,
    SendMessageRequest as SendSchema,
    RenameConversationRequest as RenameSchema,
    ConversationSummaryResponse,
    ListConversationsResponse,
    ConversationHistoryResponse,
    MessageResponse,
    SendMessageResponse,
    ChatSourceResponse,
    RenameConversationResponse,
    DeleteConversationResponse,
    SearchConversationsResponse,
    SummarizeConversationResponse,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationSummaryResponse, status_code=201)
async def create_conversation(
    body: CreateSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    project_repo = ProjectRepository(session)
    conv_repo = ConversationRepository(session)
    use_case = CreateConversationUseCase(conv_repo, project_repo, event_bus=event_bus)
    result = await use_case.execute(
        CreateConversationRequest(project_id=body.project_id, title=body.title)
    )
    return ConversationSummaryResponse(**result.__dict__)


@router.get("", response_model=ListConversationsResponse)
async def list_conversations(
    project_id: str = Query(...),
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    project_repo = ProjectRepository(session)
    conv_repo = ConversationRepository(session)
    use_case = ListConversationsUseCase(conv_repo, project_repo)
    result = await use_case.execute(project_id=project_id, skip=skip, limit=limit)
    items = [
        ConversationSummaryResponse(**c.__dict__) for c in result.conversations
    ]
    return ListConversationsResponse(conversations=items, total=result.total)


@router.get("/search", response_model=SearchConversationsResponse)
async def search_conversations(
    project_id: str = Query(...),
    q: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    project_repo = ProjectRepository(session)
    conv_repo = ConversationRepository(session)
    use_case = SearchConversationsUseCase(conv_repo, project_repo)
    result = await use_case.execute(project_id=project_id, query=q)
    items = [
        ConversationSummaryResponse(**c.__dict__) for c in result.conversations
    ]
    return SearchConversationsResponse(conversations=items, total=result.total, query=result.query)


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    conv_repo = ConversationRepository(session)
    use_case = GetConversationHistoryUseCase(conv_repo)
    result = await use_case.execute(conversation_id)
    messages = [MessageResponse(**m.__dict__) for m in result.messages]
    return ConversationHistoryResponse(
        id=result.id,
        project_id=result.project_id,
        title=result.title,
        summary=result.summary,
        messages=messages,
        message_count=result.message_count,
        total_token_count=result.total_token_count,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    body: SendSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    conv_repo = ConversationRepository(session)
    context_retriever = ContextRetriever(vector_store=in_memory_vector_store)
    llm_service = LLMService()
    use_case = SendConversationMessageUseCase(
        conv_repo, context_retriever, llm_service, event_bus=event_bus
    )
    result = await use_case.execute(
        SendMessageRequest(
            conversation_id=conversation_id,
            message=body.message,
        )
    )
    return SendMessageResponse(
        message_id=result.message_id,
        conversation_id=result.conversation_id,
        response=result.response,
        sources=[ChatSourceResponse(**s) for s in result.sources],
        token_count=result.token_count,
        message_count=result.message_count,
    )


@router.put("/{conversation_id}", response_model=RenameConversationResponse)
async def rename_conversation(
    conversation_id: str,
    body: RenameSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    conv_repo = ConversationRepository(session)
    use_case = RenameConversationUseCase(conv_repo, event_bus=event_bus)
    result = await use_case.execute(
        RenameConversationRequest(
            conversation_id=conversation_id,
            title=body.title,
        )
    )
    return RenameConversationResponse(**result.__dict__)


@router.delete("/{conversation_id}", response_model=DeleteConversationResponse)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    conv_repo = ConversationRepository(session)
    use_case = DeleteConversationUseCase(conv_repo, event_bus=event_bus)
    result = await use_case.execute(conversation_id)
    return DeleteConversationResponse(**result.__dict__)


@router.post("/{conversation_id}/summarize", response_model=SummarizeConversationResponse)
async def summarize_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    conv_repo = ConversationRepository(session)
    llm_service = LLMService()
    use_case = SummarizeConversationUseCase(conv_repo, llm_service, event_bus=event_bus)
    result = await use_case.execute(conversation_id)
    return SummarizeConversationResponse(**result.__dict__)
