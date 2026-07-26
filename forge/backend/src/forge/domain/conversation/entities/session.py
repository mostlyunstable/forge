from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from forge.domain.conversation.value_objects import SessionId, ConversationId

@dataclass
class ConversationSession:
    id: SessionId
    conversation_id: ConversationId
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    metadata: dict | None = field(default_factory=dict)

    def end_session(self) -> None:
        self.ended_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @classmethod
    def start(cls, conversation_id: ConversationId) -> ConversationSession:
        return cls(
            id=SessionId(),
            conversation_id=conversation_id
        )
