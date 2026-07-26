"""Integration tests for ConversationRepository with real database."""
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from forge.infrastructure.database.base import Base
from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    database_manager._engine = engine
    database_manager._session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield
    await engine.dispose()


@pytest.fixture
def session_factory():
    return database_manager._session_factory


async def _create_project(session: AsyncSession) -> Project:
    project_repo = ProjectRepository(session)
    project = Project.create(
        name="Test Repo",
        description="Test",
        stack=TechStack.from_list(["python"]),
    )
    await project_repo.save(project)
    return project


@pytest.mark.asyncio
async def test_save_and_get_conversation(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        conv = Conversation.create(project_id=project.id, title="Debug Session")
        conv.add_message(Message.create_user(str(conv.id), "Hello", token_count=5))
        conv.add_message(Message.create_assistant(str(conv.id), "Hi there", token_count=3))

        saved = await conv_repo.save(conv)
        await session.commit()

        fetched = await conv_repo.get_by_id(saved.id)
        assert fetched is not None
        assert fetched.title == "Debug Session"
        assert len(fetched.messages) == 2
        assert fetched.messages[0].role == "user"
        assert fetched.messages[1].content == "Hi there"


@pytest.mark.asyncio
async def test_get_by_project(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        for i in range(5):
            conv = Conversation.create(project_id=project.id, title=f"Conv {i}")
            await conv_repo.save(conv)
        await session.commit()

        results = await conv_repo.get_by_project(project.id)
        assert len(results) == 5


@pytest.mark.asyncio
async def test_delete_conversation(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        conv = Conversation.create(project_id=project.id, title="To Delete")
        conv.add_message(Message.create_user(str(conv.id), "msg", token_count=5))
        await conv_repo.save(conv)
        await session.commit()

        conv_id = conv.id
        deleted = await conv_repo.delete(conv_id)
        assert deleted is True

        fetched = await conv_repo.get_by_id(conv_id)
        assert fetched is None


@pytest.mark.asyncio
async def test_search(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        conv = Conversation.create(project_id=project.id, title="Auth debugging")
        from forge.domain.conversation.entities.summary import ConversationSummary
        summary = ConversationSummary.create(conversation_id=conv.id, content="Authentication related discussion", token_count=10)
        conv.add_summary(summary)
        await conv_repo.save(conv)
        await session.commit()

        results = await conv_repo.search(project.id, "auth")
        assert len(results) == 1
        assert "auth" in results[0].title.lower()


@pytest.mark.asyncio
async def test_count_by_project(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        for i in range(3):
            conv = Conversation.create(project_id=project.id, title=f"Conv {i}")
            await conv_repo.save(conv)
        await session.commit()

        count = await conv_repo.count_by_project(project.id)
        assert count == 3


@pytest.mark.asyncio
async def test_update_messages(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        conv = Conversation.create(project_id=project.id, title="Multi-turn")
        conv.add_message(Message.create_user(str(conv.id), "First", token_count=5))
        await conv_repo.save(conv)
        await session.commit()

        # Add more messages
        conv.add_message(Message.create_assistant(str(conv.id), "Response", token_count=3))
        conv.add_message(Message.create_user(str(conv.id), "Follow up", token_count=4))
        await conv_repo.save(conv)
        await session.commit()

        fetched = await conv_repo.get_by_id(conv.id)
        assert len(fetched.messages) == 3


@pytest.mark.asyncio
async def test_search_by_summary(session_factory):
    async with session_factory() as session:
        conv_repo = ConversationRepository(session)
        project = await _create_project(session)

        conv = Conversation.create(project_id=project.id, title="General chat")
        from forge.domain.conversation.entities.summary import ConversationSummary
        summary = ConversationSummary.create(conversation_id=conv.id, content="Discussed database indexing strategy", token_count=10)
        conv.add_summary(summary)
        await conv_repo.save(conv)
        await session.commit()

        results = await conv_repo.search(project.id, "database")
        assert len(results) == 1
