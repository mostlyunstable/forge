"""SendConversationMessageUseCase — multi-turn conversation with memory."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.events import MessageAdded, ConversationSummarized
from forge.domain.shared.events import IEventBus
from forge.application.conversation.context_builder import ContextBuilder
from forge.application.conversation.token_manager import TokenManager

logger = structlog.get_logger()


@dataclass
class SendMessageRequest:
    conversation_id: str
    message: str


@dataclass
class SendMessageResponse:
    message_id: str
    conversation_id: str
    response: str
    sources: list[dict[str, Any]]
    token_count: int
    message_count: int


class SendConversationMessageUseCase:
    """Sends a message in a multi-turn conversation.

    Orchestrates:
    1. Load conversation + history
    2. Token budget management
    3. Memory retrieval via ContextRetriever
    4. Context assembly via ContextBuilder
    5. LLM call
    6. Persist both user and assistant messages
    7. Auto-summarize if threshold exceeded
    """

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        context_retriever: Any,
        llm_service: Any,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._context_retriever = context_retriever
        self._llm_service = llm_service
        self._event_bus = event_bus
        self._context_builder = ContextBuilder()
        self._token_manager = TokenManager()

    async def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        conv_id = ConversationId.from_string(request.conversation_id)
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ConversationNotFoundError(request.conversation_id)

        # 1. Create and persist user message
        user_msg = Message.create_user(
            conversation_id=str(conv_id),
            content=request.message,
            token_count=self._token_manager.estimate_tokens(request.message),
        )
        conversation.add_message(user_msg)
        await self._conversation_repo.save(conversation)

        if self._event_bus:
            await self._event_bus.publish(
                MessageAdded(
                    conversation_id=str(conv_id),
                    role="user",
                    token_count=user_msg.token_count,
                )
            )

        # 2. Retrieve memory context
        memory_context = await self._context_retriever.retrieve(
            query=request.message,
            project_id=conversation.project_id,
        )

        # 3. Build context within token budget
        memory_tokens = self._token_manager.estimate_tokens(
            str(memory_context)
        ) if memory_context else 0

        context_window = self._token_manager.build_context_window(
            conversation, memory_tokens=memory_tokens,
        )

        llm_context = self._context_builder.build(
            conversation=conversation,
            user_message=request.message,
            memory_context=memory_context,
            max_history_tokens=context_window.message_tokens,
        )

        # 4. Call LLM
        if not self._llm_service.is_configured:
            response_text = self._format_raw_context(memory_context)
            sources = llm_context.sources
            token_count = 0
        else:
            start = time.perf_counter()
            messages = [{"role": "system", "content": llm_context.system_prompt}]
            messages.extend(llm_context.history_messages)
            messages.append({"role": "user", "content": request.message})

            llm_response = await self._llm_service.chat(messages)
            response_text = llm_response.content
            token_count = llm_response.usage.get("total_tokens", 0)
            sources = llm_context.sources

            logger.info(
                "conversation_llm_call",
                conversation_id=str(conv_id),
                duration=time.perf_counter() - start,
                tokens=token_count,
            )

        # 5. Create and persist assistant message
        assistant_msg = Message.create_assistant(
            conversation_id=str(conv_id),
            content=response_text,
            token_count=self._token_manager.estimate_tokens(response_text),
            metadata={"sources": sources, "llm_tokens": token_count},
        )
        conversation.add_message(assistant_msg)
        await self._conversation_repo.save(conversation)

        if self._event_bus:
            await self._event_bus.publish(
                MessageAdded(
                    conversation_id=str(conv_id),
                    role="assistant",
                    token_count=assistant_msg.token_count,
                )
            )

        # 6. Auto-summarize if needed
        if self._token_manager.should_summarize(conversation):
            await self._maybe_summarize(conversation)

        return SendMessageResponse(
            message_id=str(assistant_msg.id),
            conversation_id=str(conv_id),
            response=response_text,
            sources=sources,
            token_count=token_count,
            message_count=conversation.message_count,
        )

    async def _maybe_summarize(self, conversation: Conversation) -> None:
        """Summarize conversation if above threshold and LLM available."""
        if not self._llm_service.is_configured:
            return

        try:
            # Build summary from older messages
            older_messages = conversation.messages[:-10]  # keep last 10 intact
            if not older_messages:
                return

            summary_prompt = [
                {"role": "system", "content": (
                    "Summarize this engineering conversation concisely. "
                    "Focus on: decisions made, problems solved, key technical details. "
                    "Output a 2-3 paragraph summary."
                )},
            ]
            for msg in older_messages:
                summary_prompt.append({"role": msg.role, "content": msg.content})

            response = await self._llm_service.chat(summary_prompt)
            new_summary = response.content
            token_count = self._token_manager.estimate_tokens(new_summary)

            # Merge with existing summary
            if conversation.summary:
                new_summary = f"{conversation.summary}\n\n{new_summary}"
                token_count = self._token_manager.estimate_tokens(new_summary)

            conversation.set_summary(new_summary, token_count)

            # Prune old messages (keep last 10)
            pruned_count = len(conversation.messages) - 10
            conversation.messages = conversation.messages[-10:]
            conversation.message_count = len(conversation.messages)
            conversation.total_token_count = sum(
                m.token_count for m in conversation.messages
            )

            await self._conversation_repo.save(conversation)

            if self._event_bus:
                await self._event_bus.publish(
                    ConversationSummarized(
                        conversation_id=str(conversation.id),
                        message_count_pruned=pruned_count,
                    )
                )

            logger.info(
                "conversation_summarized",
                conversation_id=str(conversation.id),
                pruned=pruned_count,
            )
        except Exception as e:
            logger.warning("summarize_failed", error=str(e))

    def _format_raw_context(self, context: dict) -> str:
        """Format context when no LLM is available."""
        parts = []
        if context.get("relevant_code"):
            parts.append("**Relevant code:**")
            for r in context["relevant_code"][:5]:
                parts.append(f"- {r['payload']['name']} in {r['payload']['file_path']}")
        if context.get("relevant_decisions"):
            parts.append("\n**Related decisions:**")
            for r in context["relevant_decisions"][:5]:
                parts.append(f"- {r['payload']['title']}: {r['payload']['decision']}")
        if context.get("relevant_bugs"):
            parts.append("\n**Similar bugs resolved:**")
            for r in context["relevant_bugs"][:3]:
                parts.append(f"- {r['payload']['title']}: {r['payload'].get('solution', 'N/A')}")
        return "\n".join(parts) if parts else "No relevant context found."
