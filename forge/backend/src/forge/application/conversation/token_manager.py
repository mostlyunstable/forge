"""TokenManager — budget-aware context window management."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message

# Defaults
DEFAULT_MAX_TOKENS = 12000  # conservative budget for context window
SUMMARY_TARGET_TOKENS = 2000
RECENT_MESSAGES_BUDGET = 6000
MEMORY_BUDGET = 4000


@dataclass
class ContextWindow:
    """Represents a pruned set of messages that fits the token budget."""

    summary: str
    summary_tokens: int
    messages: list[Message]
    message_tokens: int
    total_tokens: int


class TokenManager:
    """Manages the context window to never exceed token limits.

    Strategy:
    1. Reserve budget for summary, recent messages, and memory
    2. Keep the most recent N messages that fit the budget
    3. Older messages are summarized
    """

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self._max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)

    def build_context_window(
        self,
        conversation: Conversation,
        memory_tokens: int = 0,
    ) -> ContextWindow:
        """Build a context window that fits within budget.

        Args:
            conversation: The conversation with messages.
            memory_tokens: Tokens already allocated for memory retrieval.

        Returns:
            ContextWindow with pruned messages and summary.
        """
        available = self._max_tokens - memory_tokens

        summary = conversation.summaries[-1].content if conversation.summaries else ""
        summary_tokens = conversation.summaries[-1].token_count if conversation.summaries else 0
        if not summary_tokens and summary:
            summary_tokens = self.estimate_tokens(summary)

        # Budget for messages after reserving for summary
        message_budget = available - summary_tokens
        if message_budget < 0:
            # Summary alone exceeds budget; truncate it
            max_summary_chars = available * 3  # ~4 chars/token
            summary = summary[:max_summary_chars]
            summary_tokens = self.estimate_tokens(summary)
            message_budget = 0

        # Fit as many recent messages as possible
        selected: list[Message] = []
        used_tokens = 0
        for msg in reversed(conversation.messages):
            msg_tokens = msg.token_count or self.estimate_tokens(msg.content)
            if used_tokens + msg_tokens > message_budget:
                break
            selected.append(msg)
            used_tokens += msg_tokens

        selected.reverse()

        return ContextWindow(
            summary=summary,
            summary_tokens=summary_tokens,
            messages=selected,
            message_tokens=used_tokens,
            total_tokens=summary_tokens + used_tokens,
        )

    def should_summarize(self, conversation: Conversation) -> bool:
        """Check if conversation needs summarization."""
        from forge.domain.conversation.entities.conversation import AUTO_SUMMARIZE_THRESHOLD
        return len(conversation.messages) > AUTO_SUMMARIZE_THRESHOLD
