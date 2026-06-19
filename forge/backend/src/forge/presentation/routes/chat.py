"""Chat routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.search.context_retriever import ContextRetriever
from forge.infrastructure.llm.llm_service import LLMService
from forge.application.chat.send_message import SendMessageUseCase, SendMessageRequest
from forge.presentation.deps import get_session
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.chat_schemas import (
    SendMessageRequest as ChatSchema,
    SendMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=SendMessageResponse)
async def send_message(
    body: ChatSchema,
    session: AsyncSession = Depends(get_session),
    _auth: dict = Depends(verify_token),
):
    project_repo = ProjectRepository(session)
    context_retriever = ContextRetriever()
    llm_service = LLMService()
    use_case = SendMessageUseCase(project_repo, context_retriever, llm_service)
    result = await use_case.execute(
        SendMessageRequest(
            project_id=body.project_id,
            message=body.message,
        )
    )
    return SendMessageResponse(**result.__dict__)
