from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forge.domain.conversation.value_objects import CitationId, MessageId


@dataclass
class ConversationCitation:
    """Citation for a message, keeping separation from external domains."""

    id: CitationId
    message_id: MessageId
    source_type: str
    source_reference: str
    snippet: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        message_id: MessageId,
        source_type: str,
        source_reference: str,
        snippet: str | None = None,
    ) -> ConversationCitation:
        return cls(
            id=CitationId(),
            message_id=message_id,
            source_type=source_type,
            source_reference=source_reference,
            snippet=snippet,
            metadata={},
        )
