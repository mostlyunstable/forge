"""CreateConversationUseCase."""
from __future__ import annotations

from dataclasses import dataclass

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.conversation.events import ConversationCreated
from forge.domain.shared.events import IEventBus


@dataclass
class CreateConversationRequest:
    project_id: str
    title: str


@dataclass
class CreateConversationResponse:
    id: str
    project_id: str
    title: str
    summary: str
    message_count: int
    total_token_count: int
    created_at: str
    updated_at: str


class CreateConversationUseCase:
    """Creates a new conversation for a project."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        project_repo: IProjectRepository,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._project_repo = project_repo
        self._event_bus = event_bus

    async def execute(self, request: CreateConversationRequest) -> CreateConversationResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        conversation = Conversation.create(
            project_id=project.id,
            title=request.title,
        )

        saved = await self._conversation_repo.save(conversation)

        if self._event_bus:
            await self._event_bus.publish(
                ConversationCreated(
                    conversation_id=str(saved.id),
                    project_id=str(saved.project_id),
                    title=saved.title,
                )
            )

        return CreateConversationResponse(
            id=str(saved.id),
            project_id=str(saved.project_id),
            title=saved.title,
            summary=saved.summaries[-1].content if saved.summaries else "",
            message_count=len(saved.messages),
            total_token_count=saved.total_token_count,
            created_at=saved.created_at.isoformat(),
            updated_at=saved.updated_at.isoformat(),
        )
