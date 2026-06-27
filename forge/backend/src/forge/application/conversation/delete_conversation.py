"""DeleteConversationUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.events import ConversationDeleted
from forge.domain.shared.events import IEventBus


@dataclass
class DeleteConversationResponse:
    deleted: bool
    conversation_id: str


class DeleteConversationUseCase:
    """Deletes a conversation."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._event_bus = event_bus

    async def execute(self, conversation_id: str) -> DeleteConversationResponse:
        conv_id = ConversationId.from_string(conversation_id)
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        deleted = await self._conversation_repo.delete(conv_id)

        if deleted and self._event_bus:
            await self._event_bus.publish(
                ConversationDeleted(conversation_id=conversation_id)
            )

        return DeleteConversationResponse(
            deleted=deleted,
            conversation_id=conversation_id,
        )
