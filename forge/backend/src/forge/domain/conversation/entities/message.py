"""Message entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from forge.domain.conversation.value_objects.message_id import MessageId


@dataclass
class Message:
    """A single message in a conversation."""

    id: MessageId
    conversation_id: str
    role: str  # "user", "assistant", "system"
    content: str
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {self.role}")

    @classmethod
    def create_user(cls, conversation_id: str, content: str, token_count: int = 0) -> Message:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="user",
            content=content,
            token_count=token_count,
        )

    @classmethod
    def create_assistant(cls, conversation_id: str, content: str, token_count: int = 0, metadata: dict | None = None) -> Message:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            token_count=token_count,
            metadata=metadata or {},
        )

    @classmethod
    def create_system(cls, conversation_id: str, content: str, token_count: int = 0) -> Message:
        return cls(
            id=MessageId(),
            conversation_id=conversation_id,
            role="system",
            content=content,
            token_count=token_count,
        )
