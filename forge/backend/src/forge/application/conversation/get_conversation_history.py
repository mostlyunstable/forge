"""GetConversationHistoryUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId


@dataclass
class MessageDTO:
    id: str
    role: str
    content: str
    token_count: int
    created_at: str


@dataclass
class ConversationHistoryResponse:
    id: str
    project_id: str
    title: str
    summary: str
    messages: list[MessageDTO]
    message_count: int
    total_token_count: int
    created_at: str
    updated_at: str


class GetConversationHistoryUseCase:
    """Retrieves full conversation with message history."""

    def __init__(self, conversation_repo: IConversationRepository) -> None:
        self._conversation_repo = conversation_repo

    async def execute(self, conversation_id: str, include_summary: bool = True) -> ConversationHistoryResponse:
        conv_id = ConversationId.from_string(conversation_id)
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        messages = [
            MessageDTO(
                id=str(m.id),
                role=m.role,
                content=m.content,
                token_count=m.token_count,
                created_at=m.created_at.isoformat(),
            )
            for m in conversation.messages
        ]

        return ConversationHistoryResponse(
            id=str(conversation.id),
            project_id=str(conversation.project_id),
            title=conversation.title,
            summary=(conversation.summaries[-1].content if conversation.summaries else "") if include_summary else "",
            messages=messages,
            message_count=len(conversation.messages),
            total_token_count=conversation.total_token_count,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        )
