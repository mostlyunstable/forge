"""Phase 3 API Endpoints for Conversational Engine."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from forge.application.conversation.context_manager import (
    ConversationContextManager,
    RetrievedContext,
)
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.infrastructure.events.in_memory_event_bus import event_bus
from forge.infrastructure.llm.llm_service import LLMService
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.search.context_retriever import ContextRetriever
from forge.infrastructure.search.qdrant_client import QdrantClient
from forge.presentation.deps import get_session
from fastapi.responses import StreamingResponse
import json

from forge.application.use_cases.send_message import SendMessageUseCase
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.llm.llm_service import LLMService

def get_send_message_use_case(session: AsyncSession = Depends(get_session)) -> SendMessageUseCase:
    from forge.infrastructure.search.context_retriever import ContextRetriever
    retriever = ContextRetriever(vector_store=QdrantClient())
    return SendMessageUseCase(
        conversation_repo=ConversationRepository(session),
        retriever=retriever,
        llm_provider=LLMService(),
    )

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class StartSessionRequest(BaseModel):
    project_id: str
    title: str = "New Conversation"


class StartSessionResponse(BaseModel):
    conversation_id: str
    project_id: str
    title: str


class SendMessageRequest(BaseModel):
    message: str


class Citation(BaseModel):
    source: str
    content: str
    score: float


class SendMessageResponse(BaseModel):
    conversation_id: str
    response: str
    citations: list[Citation]


@router.post("/start", response_model=StartSessionResponse, status_code=201)
async def start_session(request: StartSessionRequest, session: AsyncSession = Depends(get_session)):
    project_repo = ProjectRepository(session)
    try:
        from forge.domain.projects.value_objects.project_id import ProjectId
        proj_id = ProjectId.from_string(request.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
        
    if not await project_repo.get_by_id(proj_id):
        raise HTTPException(status_code=404, detail="Project not found")

    conv_repo = ConversationRepository(session)
    from forge.application.conversation.create_conversation import (
        CreateConversationRequest,
        CreateConversationUseCase,
    )

    use_case = CreateConversationUseCase(conv_repo, project_repo, event_bus=event_bus)
    result = await use_case.execute(
        CreateConversationRequest(project_id=request.project_id, title=request.title)
    )

    return StartSessionResponse(
        conversation_id=result.id, project_id=result.project_id, title=result.title
    )


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
    session: AsyncSession = Depends(get_session),
):
    try:
        conv_id = ConversationId.from_string(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    conv_repo = ConversationRepository(session)
    if not await conv_repo.get_by_id(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    import logging
    logger = logging.getLogger(__name__)

    async def event_generator():
        try:
            async for chunk in use_case.execute(conversation_id, request.message):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error("Streaming error", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Internal server error'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
