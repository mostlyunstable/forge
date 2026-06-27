"""ListConversationsUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class ConversationSummaryDTO:
    id: str
    project_id: str
    title: str
    summary: str
    message_count: int
    total_token_count: int
    created_at: str
    updated_at: str


@dataclass
class ListConversationsResponse:
    conversations: list[ConversationSummaryDTO]
    total: int


class ListConversationsUseCase:
    """Lists all conversations for a project."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._project_repo = project_repo

    async def execute(self, project_id: str, skip: int = 0, limit: int = 50) -> ListConversationsResponse:
        pid = ProjectId.from_string(project_id)
        project = await self._project_repo.get_by_id(pid)
        if not project:
            raise ProjectNotFoundError(project_id)

        conversations = await self._conversation_repo.get_by_project(pid, skip=skip, limit=limit)
        total = await self._conversation_repo.count_by_project(pid)

        items = [
            ConversationSummaryDTO(
                id=str(c.id),
                project_id=str(c.project_id),
                title=c.title,
                summary=c.summary[:200] if c.summary else "",
                message_count=c.message_count,
                total_token_count=c.total_token_count,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in conversations
        ]

        return ListConversationsResponse(conversations=items, total=total)
