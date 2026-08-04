"""Conversation domain events."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.shared.events import DomainEvent


@dataclass(frozen=True)
class ConversationCreated(DomainEvent):
    """Published when a conversation is created."""

    conversation_id: str = ""
    project_id: str = ""
    title: str = ""

    @property
    def event_type(self) -> str:
        return "conversation.created"

    def to_dict(self):
        base = super().to_dict()
        base["conversation_id"] = self.conversation_id
        base["project_id"] = self.project_id
        base["title"] = self.title
        return base


@dataclass(frozen=True)
class MessageAdded(DomainEvent):
    """Published when a message is added to a conversation."""

    conversation_id: str = ""
    role: str = ""
    token_count: int = 0

    @property
    def event_type(self) -> str:
        return "conversation.message_added"

    def to_dict(self):
        base = super().to_dict()
        base["conversation_id"] = self.conversation_id
        base["role"] = self.role
        base["token_count"] = self.token_count
        return base


@dataclass(frozen=True)
class ConversationRenamed(DomainEvent):
    """Published when a conversation is renamed."""

    conversation_id: str = ""
    new_title: str = ""

    @property
    def event_type(self) -> str:
        return "conversation.renamed"

    def to_dict(self):
        base = super().to_dict()
        base["conversation_id"] = self.conversation_id
        base["new_title"] = self.new_title
        return base


@dataclass(frozen=True)
class ConversationDeleted(DomainEvent):
    """Published when a conversation is deleted."""

    conversation_id: str = ""

    @property
    def event_type(self) -> str:
        return "conversation.deleted"

    def to_dict(self):
        base = super().to_dict()
        base["conversation_id"] = self.conversation_id
        return base


@dataclass(frozen=True)
class ConversationSummarized(DomainEvent):
    """Published when a conversation is summarized."""

    conversation_id: str = ""
    message_count_pruned: int = 0

    @property
    def event_type(self) -> str:
        return "conversation.summarized"

    def to_dict(self):
        base = super().to_dict()
        base["conversation_id"] = self.conversation_id
        base["message_count_pruned"] = self.message_count_pruned
        return base
