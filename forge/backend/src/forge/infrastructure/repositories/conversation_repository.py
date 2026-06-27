"""ConversationRepository - implements IConversationRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.value_objects.message_id import MessageId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.conversation_model import ConversationModel
from forge.infrastructure.database.models.message_model import MessageModel


class ConversationRepository(IConversationRepository):
    """SQLAlchemy implementation of IConversationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.id == str(conversation_id.value)
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        # Load messages
        msg_result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == str(conversation_id.value))
            .order_by(MessageModel.created_at)
        )
        msg_models = msg_result.scalars().all()

        return self._to_domain(model, msg_models)

    async def get_by_project(
        self, project_id: ProjectId, skip: int = 0, limit: int = 50
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(ConversationModel)
            .where(ConversationModel.project_id == str(project_id.value))
            .order_by(ConversationModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, conversation: Conversation) -> Conversation:
        # Upsert conversation
        model = await self._session.get(
            ConversationModel, str(conversation.id.value)
        )
        if model:
            model.title = conversation.title
            model.summary = conversation.summary
            model.summary_token_count = conversation.summary_token_count
            model.total_token_count = conversation.total_token_count
            model.message_count = conversation.message_count
            model.updated_at = conversation.updated_at
        else:
            model = self._to_model(conversation)
            self._session.add(model)

        # Sync messages: delete existing, re-insert
        existing = await self._session.execute(
            select(MessageModel).where(
                MessageModel.conversation_id == str(conversation.id.value)
            )
        )
        for old_msg in existing.scalars().all():
            await self._session.delete(old_msg)

        for msg in conversation.messages:
            msg_model = MessageModel(
                id=str(msg.id),
                conversation_id=str(conversation.id.value),
                role=msg.role,
                content=msg.content,
                token_count=msg.token_count,
                metadata_json=msg.metadata if msg.metadata else None,
                created_at=msg.created_at,
            )
            self._session.add(msg_model)

        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, conversation_id: ConversationId) -> bool:
        # Delete messages first
        from sqlalchemy import delete as sql_delete
        await self._session.execute(
            sql_delete(MessageModel).where(
                MessageModel.conversation_id == str(conversation_id.value)
            )
        )

        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.id == str(conversation_id.value)
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    async def search(self, project_id: ProjectId, query: str) -> list[Conversation]:
        safe_pattern = f"%{query}%"
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.project_id == str(project_id.value),
                (ConversationModel.title.ilike(safe_pattern))
                | (ConversationModel.summary.ilike(safe_pattern)),
            )
            .order_by(ConversationModel.updated_at.desc())
            .limit(50)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_project(self, project_id: ProjectId) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(ConversationModel).where(
                ConversationModel.project_id == str(project_id.value)
            )
        )
        return result.scalar_one()

    def _to_domain(self, model: ConversationModel, msg_models=None) -> Conversation:
        from uuid import UUID
        messages = []
        if msg_models:
            messages = [
                Message(
                    id=MessageId(UUID(m.id)),
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    token_count=m.token_count or 0,
                    metadata=m.metadata_json or {},
                    created_at=m.created_at,
                )
                for m in msg_models
            ]

        return Conversation(
            id=ConversationId(UUID(model.id)),
            project_id=ProjectId(UUID(model.project_id)),
            title=model.title,
            messages=messages,
            summary=model.summary or "",
            summary_token_count=model.summary_token_count or 0,
            total_token_count=model.total_token_count or 0,
            message_count=model.message_count or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Conversation) -> ConversationModel:
        return ConversationModel(
            id=str(entity.id.value),
            project_id=str(entity.project_id.value),
            title=entity.title,
            summary=entity.summary,
            summary_token_count=entity.summary_token_count,
            total_token_count=entity.total_token_count,
            message_count=entity.message_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
