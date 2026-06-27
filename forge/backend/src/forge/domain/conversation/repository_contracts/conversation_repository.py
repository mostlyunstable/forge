"""IConversationRepository - contract for conversation persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.projects.value_objects.project_id import ProjectId


class IConversationRepository(ABC):
    """Interface for conversation persistence."""

    @abstractmethod
    async def get_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        """Retrieve a conversation by its ID."""

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId, skip: int = 0, limit: int = 50) -> list[Conversation]:
        """Retrieve conversations for a project, newest first."""

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        """Persist a new or updated conversation."""

    @abstractmethod
    async def delete(self, conversation_id: ConversationId) -> bool:
        """Delete a conversation by ID."""

    @abstractmethod
    async def search(self, project_id: ProjectId, query: str) -> list[Conversation]:
        """Search conversations by title or content."""

    @abstractmethod
    async def count_by_project(self, project_id: ProjectId) -> int:
        """Count conversations for a project."""
