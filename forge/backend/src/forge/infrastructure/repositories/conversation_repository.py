# mypy: disable-error-code="assignment, arg-type"
"""ConversationRepository - implements IConversationRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from forge.domain.conversation.entities.citation import ConversationCitation
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import ConversationMessage
from forge.domain.conversation.entities.session import ConversationSession
from forge.domain.conversation.entities.summary import ConversationSummary
from forge.domain.conversation.repository_contracts.conversation_repository import (
    IConversationRepository,
)
from forge.domain.conversation.value_objects.citation_id import CitationId
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.value_objects.conversation_state import ConversationState
from forge.domain.conversation.value_objects.message_id import MessageId
from forge.domain.conversation.value_objects.session_id import SessionId
from forge.domain.conversation.value_objects.summary_id import SummaryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.conversation_citation_model import (
    ConversationCitationModel,
)
from forge.infrastructure.database.models.conversation_model import ConversationModel
from forge.infrastructure.database.models.conversation_session_model import ConversationSessionModel
from forge.infrastructure.database.models.conversation_summary_model import ConversationSummaryModel
from forge.infrastructure.database.models.message_model import MessageModel


class ConversationRepository(IConversationRepository):
    """SQLAlchemy implementation of IConversationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel)
            .options(
                selectinload(ConversationModel.messages).selectinload(MessageModel.citations),
                selectinload(ConversationModel.sessions),
                selectinload(ConversationModel.summaries),
            )
            .where(ConversationModel.id == str(conversation_id.value))
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_project(
        self, project_id: ProjectId, skip: int = 0, limit: int = 50
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(ConversationModel)
            .options(
                selectinload(ConversationModel.messages).selectinload(MessageModel.citations),
                selectinload(ConversationModel.sessions),
                selectinload(ConversationModel.summaries),
            )
            .where(ConversationModel.project_id == str(project_id.value))
            .order_by(ConversationModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, conversation: Conversation) -> Conversation:
        model = await self._session.get(ConversationModel, str(conversation.id.value))
        import json

        if model:
            model.title = conversation.title
            model.state = conversation.state.value
            model.total_token_count = conversation.total_token_count
            model.metadata_ = json.dumps(conversation.metadata)
            model.updated_at = conversation.updated_at
        else:
            model = ConversationModel(
                id=str(conversation.id.value),
                project_id=str(conversation.project_id.value),
                title=conversation.title,
                state=conversation.state.value,
                total_token_count=conversation.total_token_count,
                metadata_=json.dumps(conversation.metadata),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            self._session.add(model)

        # Find existing IDs
        existing_msg_ids = {
            row[0] for row in (
                await self._session.execute(
                    select(MessageModel.id).where(MessageModel.conversation_id == str(conversation.id.value))
                )
            ).fetchall()
        }
        existing_session_ids = {
            row[0] for row in (
                await self._session.execute(
                    select(ConversationSessionModel.id).where(ConversationSessionModel.conversation_id == str(conversation.id.value))
                )
            ).fetchall()
        }
        existing_summary_ids = {
            row[0] for row in (
                await self._session.execute(
                    select(ConversationSummaryModel.id).where(ConversationSummaryModel.conversation_id == str(conversation.id.value))
                )
            ).fetchall()
        }

        # Insert new models
        for session in conversation.sessions:
            if str(session.id.value) not in existing_session_ids:
                sess_model = ConversationSessionModel(
                    id=str(session.id.value),
                    conversation_id=str(conversation.id.value),
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                    metadata_json=session.metadata,
                )
                self._session.add(sess_model)

        for summary in conversation.summaries:
            if str(summary.id.value) not in existing_summary_ids:
                sum_model = ConversationSummaryModel(
                    id=str(summary.id.value),
                    conversation_id=str(conversation.id.value),
                    content=summary.content,
                    token_count=summary.token_count,
                    created_at=summary.created_at,
                )
                self._session.add(sum_model)

        for msg in conversation.messages:
            if str(msg.id.value) not in existing_msg_ids:
                msg_model = MessageModel(
                    id=str(msg.id.value),
                    conversation_id=str(conversation.id.value),
                    role=msg.role,
                    content=msg.content,
                    token_count=msg.token_count,
                    metadata_json=msg.metadata if msg.metadata else {},
                    created_at=msg.created_at,
                )
                self._session.add(msg_model)
                for cit in msg.citations:
                    cit_model = ConversationCitationModel(
                        id=str(cit.id.value),
                        message_id=str(msg.id.value),
                        source_type=cit.source_type,
                        source_reference=cit.source_reference,
                        snippet=cit.snippet,
                        metadata_json=cit.metadata if cit.metadata else {},
                    )
                    self._session.add(cit_model)

        await self._session.flush()
        return conversation

    async def delete(self, conversation_id: ConversationId) -> bool:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == str(conversation_id.value))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    async def search(self, project_id: ProjectId, query: str) -> list[Conversation]:
        safe_pattern = f"%{query}%"
        # Search in title, messages, or summaries
        result = await self._session.execute(
            select(ConversationModel)
            .options(
                selectinload(ConversationModel.messages).selectinload(MessageModel.citations),
                selectinload(ConversationModel.sessions),
                selectinload(ConversationModel.summaries),
            )
            .outerjoin(ConversationModel.messages)
            .outerjoin(ConversationModel.summaries)
            .where(
                ConversationModel.project_id == str(project_id.value),
                (ConversationModel.title.ilike(safe_pattern))
                | (MessageModel.content.ilike(safe_pattern))
                | (ConversationSummaryModel.content.ilike(safe_pattern)),
            )
            .group_by(ConversationModel.id)
            .order_by(ConversationModel.updated_at.desc())
            .limit(50)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_project(self, project_id: ProjectId) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(ConversationModel)
            .where(ConversationModel.project_id == str(project_id.value))
        )
        return result.scalar_one()

    def _to_domain(self, model: ConversationModel) -> Conversation:
        sessions = [
            ConversationSession(
                id=SessionId(UUID(s.id)),
                conversation_id=ConversationId(UUID(s.conversation_id)),
                started_at=s.started_at,
                ended_at=s.ended_at,
                metadata=s.metadata_json or {},
            )
            for s in model.sessions
        ]

        summaries = [
            ConversationSummary(
                id=SummaryId(UUID(sm.id)),
                conversation_id=ConversationId(UUID(sm.conversation_id)),
                content=sm.content,
                token_count=sm.token_count,
                created_at=sm.created_at,
            )
            for sm in model.summaries
        ]

        messages = []
        for m in model.messages:
            citations = [
                ConversationCitation(
                    id=CitationId(UUID(c.id)),
                    message_id=MessageId(UUID(c.message_id)),
                    source_type=c.source_type,
                    source_reference=c.source_reference,
                    snippet=c.snippet,
                    metadata=c.metadata_json or {},
                )
                for c in m.citations
            ]
            msg = ConversationMessage(
                id=MessageId(UUID(m.id)),
                conversation_id=ConversationId(UUID(m.conversation_id)),
                role=m.role,
                content=m.content,
                token_count=m.token_count or 0,
                citations=citations,
                metadata=m.metadata_json or {},
                created_at=m.created_at,
            )
            messages.append(msg)

        return Conversation(
            id=ConversationId(UUID(model.id)),
            project_id=ProjectId(UUID(model.project_id)),
            title=model.title,
            state=ConversationState(model.state),
            messages=messages,
            sessions=sessions,
            summaries=summaries,
            total_token_count=model.total_token_count or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
