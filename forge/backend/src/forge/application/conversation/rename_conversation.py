"""RenameConversationUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.events import ConversationRenamed
from forge.domain.shared.events import IEventBus


@dataclass
class RenameConversationRequest:
    conversation_id: str
    title: str


@dataclass
class RenameConversationResponse:
    id: str
    title: str
    updated_at: str


class RenameConversationUseCase:
    """Renames a conversation."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._event_bus = event_bus

    async def execute(self, request: RenameConversationRequest) -> RenameConversationResponse:
        conv_id = ConversationId.from_string(request.conversation_id)
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ConversationNotFoundError(request.conversation_id)

        conversation.rename(request.title)
        saved = await self._conversation_repo.save(conversation)

        if self._event_bus:
            await self._event_bus.publish(
                ConversationRenamed(
                    conversation_id=str(saved.id),
                    new_title=saved.title,
                )
            )

        return RenameConversationResponse(
            id=str(saved.id),
            title=saved.title,
            updated_at=saved.updated_at.isoformat(),
        )
