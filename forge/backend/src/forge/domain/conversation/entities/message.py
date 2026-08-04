from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from forge.domain.conversation.entities.citation import ConversationCitation
from forge.domain.conversation.value_objects import ConversationId, MessageId


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    id: MessageId
    conversation_id: ConversationId
    role: str  # "user", "assistant", "system"
    content: str
    token_count: int = 0
    citations: list[ConversationCitation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant", "system", "tool"):
            raise ValueError(f"Invalid role: {self.role}")

    def add_citation(self, citation: ConversationCitation) -> None:
        self.citations.append(citation)

    @classmethod
    def create_user(
        cls,
        conversation_id: ConversationId,
        content: str,
        token_count: int = 0,
        metadata: dict | None = None,
    ) -> ConversationMessage:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="user",
            content=content,
            token_count=token_count,
            metadata=metadata or {},
        )

    @classmethod
    def create_assistant(
        cls,
        conversation_id: ConversationId,
        content: str | None = None,
        tool_calls: list[dict] | None = None,
        token_count: int = 0,
        metadata: dict | None = None,
    ) -> ConversationMessage:
        meta = metadata or {}
        if tool_calls:
            meta["tool_calls"] = tool_calls

        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="assistant",
            content=content or "",
            token_count=token_count,
            metadata=meta,
        )

    @classmethod
    def create_system(
        cls, conversation_id: ConversationId, content: str, token_count: int = 0
    ) -> ConversationMessage:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="system",
            content=content,
            token_count=token_count,
        )

    @classmethod
    def create_tool(
        cls,
        conversation_id: ConversationId,
        content: str,
        tool_call_id: str,
        name: str,
        token_count: int = 0,
    ) -> ConversationMessage:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="tool",
            content=content,
            token_count=token_count,
            metadata={"tool_call_id": tool_call_id, "name": name},
        )


# Alias for backward compatibility during refactor
Message = ConversationMessage
