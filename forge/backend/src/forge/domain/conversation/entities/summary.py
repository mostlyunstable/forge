from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from forge.domain.conversation.value_objects import ConversationId, SummaryId


@dataclass
class ConversationSummary:
    id: SummaryId
    conversation_id: ConversationId
    content: str
    token_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls, conversation_id: ConversationId, content: str, token_count: int
    ) -> ConversationSummary:
        return cls(
            id=SummaryId(),
            conversation_id=conversation_id,
            content=content,
            token_count=token_count,
        )
