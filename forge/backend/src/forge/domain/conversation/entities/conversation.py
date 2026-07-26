"""Conversation aggregate root."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from forge.domain.conversation.entities.message import ConversationMessage
from forge.domain.conversation.entities.session import ConversationSession
from forge.domain.conversation.entities.summary import ConversationSummary
from forge.domain.conversation.value_objects import ConversationId, ConversationState
from forge.domain.projects.value_objects.project_id import ProjectId

# Maximum messages before auto-summarize is triggered
AUTO_SUMMARIZE_THRESHOLD = 20


@dataclass
class Conversation:
    """Conversation aggregate root. Owns messages, sessions, summaries, and lifecycle."""

    id: ConversationId
    project_id: ProjectId
    title: str
    state: ConversationState = ConversationState.ACTIVE
    messages: list[ConversationMessage] = field(default_factory=list)
    sessions: list[ConversationSession] = field(default_factory=list)
    summaries: list[ConversationSummary] = field(default_factory=list)
    total_token_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the conversation."""
        if self.state == ConversationState.ARCHIVED:
            raise ValueError("Cannot add message to an archived conversation.")
        
        self.messages.append(message)
        self.total_token_count += message.token_count
        self.updated_at = datetime.now(timezone.utc)
        self.state = ConversationState.ACTIVE

    def start_session(self) -> ConversationSession:
        """Start a new session."""
        if self.state == ConversationState.ARCHIVED:
            raise ValueError("Cannot start session in an archived conversation.")
        
        # End any currently active session
        if self.active_session:
            self.active_session.end_session()
            
        session = ConversationSession.start(self.id)
        self.sessions.append(session)
        self.updated_at = datetime.now(timezone.utc)
        self.state = ConversationState.ACTIVE
        return session

    def end_active_session(self) -> None:
        if self.active_session:
            self.active_session.end_session()
            self.updated_at = datetime.now(timezone.utc)
            self.state = ConversationState.IDLE

    @property
    def active_session(self) -> ConversationSession | None:
        """Return the currently active session, if any."""
        if not self.sessions:
            return None
        last_session = self.sessions[-1]
        return last_session if last_session.is_active else None

    def add_summary(self, summary: ConversationSummary) -> None:
        """Add a summary to the conversation."""
        if self.state == ConversationState.ARCHIVED:
            raise ValueError("Cannot summarize an archived conversation.")
            
        self.summaries.append(summary)
        self.updated_at = datetime.now(timezone.utc)
        self.state = ConversationState.SUMMARIZED

    def archive(self) -> None:
        """Archive the conversation."""
        self.end_active_session()
        self.state = ConversationState.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)

    def mark_idle(self) -> None:
        """Mark the conversation as idle."""
        if self.state == ConversationState.ARCHIVED:
            raise ValueError("Cannot mark an archived conversation as idle.")
        self.end_active_session()
        self.state = ConversationState.IDLE
        self.updated_at = datetime.now(timezone.utc)

    def rename(self, title: str) -> None:
        """Rename the conversation."""
        self.title = title
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def create(cls, project_id: ProjectId, title: str) -> Conversation:
        conv = cls(
            id=ConversationId(),
            project_id=project_id,
            title=title,
            state=ConversationState.ACTIVE
        )
        return conv
