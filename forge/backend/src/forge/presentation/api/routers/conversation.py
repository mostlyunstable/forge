"""Phase 3 API Endpoints for Conversational Engine."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.presentation.deps import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from forge.application.conversation.context_manager import ConversationContextManager, RetrievedContext
from forge.infrastructure.search.context_retriever import ContextRetriever
from forge.infrastructure.search.qdrant_client import QdrantClient
from forge.infrastructure.llm.llm_service import LLMService
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.domain.conversation.entities.message import Message
from forge.application.conversation.token_manager import ContextWindow
from forge.infrastructure.events.in_memory_event_bus import event_bus

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
async def start_session(
    request: StartSessionRequest,
    session: AsyncSession = Depends(get_session)
):
    project_repo = ProjectRepository(session)
    if not await project_repo.get_by_id(request.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
        
    conv_repo = ConversationRepository(session)
    from forge.application.conversation.create_conversation import CreateConversationUseCase, CreateConversationRequest
    use_case = CreateConversationUseCase(conv_repo, project_repo, event_bus=event_bus)
    result = await use_case.execute(CreateConversationRequest(project_id=request.project_id, title=request.title))
    
    return StartSessionResponse(
        conversation_id=result.id,
        project_id=result.project_id,
        title=result.title
    )

@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    session: AsyncSession = Depends(get_session)
):
    conv_repo = ConversationRepository(session)
    try:
        conv_id = ConversationId.from_string(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
    conversation = await conv_repo.get_by_id(conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_msg = Message.create_user(
        conversation_id=conversation_id,
        content=request.message,
        token_count=max(1, len(request.message) // 4)
    )
    conversation.add_message(user_msg)
    await conv_repo.save(conversation)
    
    retriever = ContextRetriever(vector_store=QdrantClient())
    retrieval_result = await retriever.retrieve(
        query=request.message,
        project_id=conversation.project_id,
        context_window=None
    )
    
    retrieved_contexts = []
    for t in ["relevant_code", "relevant_decisions", "relevant_bugs"]:
        for res in retrieval_result.get(t, []):
            content = res.get("payload", {}).get("content", "")
            source = res.get("payload", {}).get("file_path", "") or res.get("payload", {}).get("title", "") or "unknown"
            retrieved_contexts.append(
                RetrievedContext(source=source, content=content, score=res.get("score", 1.0))
            )

    context_manager = ConversationContextManager(conv_repo)
    assembled_context = await context_manager.build_context(conv_id, retrieved_contexts)
    
    messages_for_llm = []
    for m in assembled_context["messages"]:
        if m["role"] == "user":
            messages_for_llm.append(Message.create_user(conversation_id=conversation_id, content=m["content"], token_count=1))
        elif m["role"] == "assistant":
            messages_for_llm.append(Message.create_assistant(conversation_id=conversation_id, content=m["content"], token_count=1))
    
    context_window = ContextWindow(
        summary=assembled_context["summary"],
        summary_tokens=0,
        messages=messages_for_llm,
        message_tokens=0,
        total_tokens=assembled_context["total_tokens_estimated"]
    )
    
    retrieved_context_str = "\n\n".join([
        f"Source: {ctx['source']}\n{ctx['content']}" for ctx in assembled_context["retrieved"]
    ])
    
    llm_service = LLMService()
    reasoning_engine = ReasoningEngine(llm_provider=llm_service)
    
    response_text = await reasoning_engine.generate_response(
        context_window=context_window,
        retrieved_context=retrieved_context_str
    )
    
    assistant_msg = Message.create_assistant(
        conversation_id=conversation_id,
        content=response_text,
        token_count=max(1, len(response_text) // 4)
    )
    conversation.add_message(assistant_msg)
    await conv_repo.save(conversation)
    
    citations = [
        Citation(source=ctx["source"], content=ctx["content"], score=ctx["score"])
        for ctx in assembled_context["retrieved"]
    ]
    
    return SendMessageResponse(
        conversation_id=conversation_id,
        response=response_text,
        citations=citations
    )
