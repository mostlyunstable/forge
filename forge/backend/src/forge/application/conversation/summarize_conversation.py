"""SummarizeConversationUseCase — manual summarization trigger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.events import ConversationSummarized
from forge.domain.shared.events import IEventBus
from forge.application.conversation.token_manager import TokenManager

logger = structlog.get_logger()


@dataclass
class SummarizeConversationResponse:
    conversation_id: str
    summary: str
    message_count_pruned: int


class SummarizeConversationUseCase:
    """Manually triggers conversation summarization."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        llm_service: Any,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._llm_service = llm_service
        self._event_bus = event_bus
        self._token_manager = TokenManager()

    async def execute(self, conversation_id: str) -> SummarizeConversationResponse:
        conv_id = ConversationId.from_string(conversation_id)
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        if not self._llm_service.is_configured:
            return SummarizeConversationResponse(
                conversation_id=conversation_id,
                summary=conversation.summary,
                message_count_pruned=0,
            )

        try:
            summary_prompt = [
                {"role": "system", "content": (
                    "Summarize this engineering conversation concisely. "
                    "Focus on: decisions made, problems solved, key technical details. "
                    "Output a 2-3 paragraph summary."
                )},
            ]
            for msg in conversation.messages:
                summary_prompt.append({"role": msg.role, "content": msg.content})

            response = await self._llm_service.chat(summary_prompt)
            new_summary = response.content
            token_count = self._token_manager.estimate_tokens(new_summary)

            conversation.set_summary(new_summary, token_count)
            saved = await self._conversation_repo.save(conversation)

            if self._event_bus:
                await self._event_bus.publish(
                    ConversationSummarized(
                        conversation_id=str(saved.id),
                        message_count_pruned=0,
                    )
                )

            return SummarizeConversationResponse(
                conversation_id=conversation_id,
                summary=new_summary,
                message_count_pruned=0,
            )
        except Exception as e:
            logger.warning("manual_summarize_failed", error=str(e))
            return SummarizeConversationResponse(
                conversation_id=conversation_id,
                summary=conversation.summary,
                message_count_pruned=0,
            )
