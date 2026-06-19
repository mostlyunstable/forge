"""Chat routes."""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.search.embedding_service import EmbeddingService
from forge.infrastructure.llm.llm_service import LLMService
from forge.application.chat.send_message import SendMessageUseCase, SendMessageRequest
from forge.presentation.deps import get_session, get_vector_store
from forge.presentation.middleware.auth import verify_token
from forge.presentation.schemas.chat_schemas import (
    SendMessageRequest as ChatSchema,
    SendMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


class ContextRetriever:
    """Adapter that bridges the use case port to infrastructure."""

    def __init__(self, vector_store: Any = None) -> None:
        self._embedding_service = EmbeddingService()
        self._vector_store = vector_store or get_vector_store()

    async def retrieve(self, query: str, project_id) -> dict:
        query_embedding = await self._embedding_service.get_embedding(query)
        project_uuid = project_id.value if hasattr(project_id, "value") else project_id
        code = await self._vector_store.search_code(query_embedding, project_uuid, limit=5)
        decisions = await self._vector_store.search_decisions(query_embedding, project_uuid, limit=5)
        bugs = await self._vector_store.search_bugs(query_embedding, project_uuid, limit=3)
        return {
            "relevant_code": code,
            "relevant_decisions": decisions,
            "relevant_bugs": bugs,
        }


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
