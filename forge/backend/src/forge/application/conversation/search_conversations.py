"""SearchConversationsUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.repository_contracts.conversation_repository import (
    IConversationRepository,
)
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
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
class SearchConversationsResponse:
    conversations: list[ConversationSummaryDTO]
    total: int
    query: str


class SearchConversationsUseCase:
    """Searches conversations by title or content."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        project_repo: IProjectRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._project_repo = project_repo

    async def execute(self, project_id: str, query: str) -> SearchConversationsResponse:
        pid = ProjectId.from_string(project_id)
        project = await self._project_repo.get_by_id(pid)
        if not project:
            raise ProjectNotFoundError(project_id)

        results = await self._conversation_repo.search(pid, query)

        conversations = [
            ConversationSummaryDTO(
                id=str(c.id),
                project_id=str(c.project_id),
                title=c.title,
                summary=c.summaries[-1].content if c.summaries else "",
                message_count=len(c.messages),
                total_token_count=c.total_token_count,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in results
        ]

        return SearchConversationsResponse(
            conversations=conversations,
            total=len(conversations),
            query=query,
        )
