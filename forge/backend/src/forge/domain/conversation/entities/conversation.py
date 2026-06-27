"""Conversation aggregate root."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.projects.value_objects.project_id import ProjectId

# Maximum messages before auto-summarize is triggered
AUTO_SUMMARIZE_THRESHOLD = 20


@dataclass
class Conversation:
    """Conversation aggregate root. Owns messages and lifecycle."""

    id: ConversationId
    project_id: ProjectId
    title: str
    messages: list[Message] = field(default_factory=list)
    summary: str = ""
    summary_token_count: int = 0
    total_token_count: int = 0
    message_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.total_token_count += message.token_count
        self.message_count = len(self.messages)
        self.updated_at = datetime.now(timezone.utc)

    def set_summary(self, summary: str, token_count: int) -> None:
        """Set a conversation summary (after pruning older messages)."""
        self.summary = summary
        self.summary_token_count = token_count

    def needs_summarize(self) -> bool:
        """Check if conversation exceeds auto-summarize threshold."""
        return self.message_count > AUTO_SUMMARIZE_THRESHOLD

    def rename(self, title: str) -> None:
        """Rename the conversation."""
        self.title = title
        self.updated_at = datetime.now(timezone.utc)

    @property
    def recent_messages(self) -> list[Message]:
        """Return the most recent messages (after any summary)."""
        return self.messages[-20:]

    @classmethod
    def create(cls, project_id: ProjectId, title: str) -> Conversation:
        return cls(
            id=ConversationId(),
            project_id=project_id,
            title=title,
        )
