"""ConversationContextManager - coordinates context assembly for LLMs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from forge.application.conversation.token_manager import TokenManager
from forge.domain.conversation.repository_contracts.conversation_repository import (
    IConversationRepository,
)
from forge.domain.conversation.value_objects.conversation_id import ConversationId


@dataclass
class RetrievedContext:
    """A chunk of context retrieved from Memory, Graph, or other sources."""

    source: str
    content: str
    score: float = 1.0


class ConversationContextManager:
    """Builds and manages conversation context."""

    def __init__(
        self, conversation_repo: IConversationRepository, token_manager: TokenManager | None = None
    ):
        self._repo = conversation_repo
        self._token_manager = token_manager or TokenManager()

    async def build_context(
        self, conversation_id: ConversationId, retrieved_contexts: list[RetrievedContext]
    ) -> dict[str, Any]:
        """Builds a token-budgeted, deduplicated context window for the LLM.

        Args:
            conversation_id: ID of the conversation to build context for.
            retrieved_contexts: List of context chunks retrieved from other systems.

        Returns:
            A dictionary containing the assembled context.
        """
        conversation = await self._repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found.")

        # 1. Deduplicate retrieved contexts deterministically
        deduped = self._deduplicate_and_sort_contexts(retrieved_contexts)

        # 2. Calculate tokens used by retrieved context
        retrieved_tokens = sum(self._token_manager.estimate_tokens(ctx.content) for ctx in deduped)

        # 3. Compress conversation messages using token manager
        # TokenManager manages summary and recent messages within the remaining budget.
        context_window = self._token_manager.build_context_window(
            conversation=conversation, memory_tokens=retrieved_tokens
        )

        # 4. Assemble the final context deterministically
        return {
            "summary": context_window.summary,
            "messages": [
                {"role": msg.role, "content": msg.content, "metadata": msg.metadata}
                for msg in context_window.messages
            ],
            "retrieved": [
                {"source": ctx.source, "content": ctx.content, "score": ctx.score}
                for ctx in deduped
            ],
            "total_tokens_estimated": context_window.total_tokens + retrieved_tokens,
        }

    def _deduplicate_and_sort_contexts(
        self, contexts: list[RetrievedContext]
    ) -> list[RetrievedContext]:
        """Deduplicate chunks by content hash and sort deterministically."""
        seen_hashes = set()
        deduped = []

        for ctx in contexts:
            content_hash = hashlib.sha256(ctx.content.encode("utf-8")).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduped.append(ctx)

        # Sort primarily by score (descending), then by content hash for determinism
        deduped.sort(
            key=lambda x: (-x.score, hashlib.sha256(x.content.encode("utf-8")).hexdigest())
        )
        return deduped
