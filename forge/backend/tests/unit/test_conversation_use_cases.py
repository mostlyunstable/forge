"""Unit tests for Conversation application use cases."""

from dataclasses import dataclass

import pytest

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import ConversationMessage as Message
from forge.domain.conversation.exceptions import ConversationNotFoundError
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.value_objects.message_id import MessageId
from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from tests.conftest import FakeConversationRepo, FakeProjectRepo

# --- Fake LLM ---


@dataclass
class FakeLLMResponse:
    content: str
    model: str = "test-model"
    usage: dict = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}


class FakeLLMService:
    def __init__(self, response_text: str = "Test response"):
        self._response_text = response_text
        self._configured = True

    @property
    def is_configured(self):
        return self._configured

    async def chat(self, messages, temperature=0.7, max_tokens=4096):
        return FakeLLMResponse(content=self._response_text)


class FakeContextRetriever:
    async def retrieve(self, query, project_id, context_window=None):
        return {
            "relevant_code": [],
            "relevant_decisions": [],
            "relevant_bugs": [],
        }


# --- Tests ---


class TestCreateConversationUseCase:
    @pytest.mark.asyncio
    async def test_create_conversation(self):
        from forge.application.conversation.create_conversation import (
            CreateConversationRequest,
            CreateConversationUseCase,
        )

        project_repo = FakeProjectRepo()
        conv_repo = FakeConversationRepo()

        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        await project_repo.save(project)

        use_case = CreateConversationUseCase(conv_repo, project_repo)
        result = await use_case.execute(
            CreateConversationRequest(
                project_id=str(project.id),
                title="My conversation",
            )
        )
        assert result.title == "My conversation"
        assert result.project_id == str(project.id)
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_conversation_project_not_found(self):
        from forge.application.conversation.create_conversation import (
            CreateConversationRequest,
            CreateConversationUseCase,
        )

        project_repo = FakeProjectRepo()
        conv_repo = FakeConversationRepo()

        use_case = CreateConversationUseCase(conv_repo, project_repo)
        with pytest.raises(Exception):
            await use_case.execute(
                CreateConversationRequest(
                    project_id=str(ProjectId()),
                    title="Test",
                )
            )


class TestGetConversationHistoryUseCase:
    @pytest.mark.asyncio
    async def test_get_history(self):
        from forge.application.conversation.get_conversation_history import (
            GetConversationHistoryUseCase,
        )

        conv_repo = FakeConversationRepo()

        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        conv = Conversation.create(project_id=project.id, title="Test Conv")
        conv.add_message(Message.create_user(str(conv.id), "Hello", token_count=5))
        conv.add_message(Message.create_assistant(str(conv.id), "Hi", token_count=3))
        await conv_repo.save(conv)

        use_case = GetConversationHistoryUseCase(conv_repo)
        result = await use_case.execute(str(conv.id))
        assert result.title == "Test Conv"
        assert len(result.messages) == 2
        assert result.messages[0].role == "user"
        assert result.messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_get_history_not_found(self):
        from forge.application.conversation.get_conversation_history import (
            GetConversationHistoryUseCase,
        )

        conv_repo = FakeConversationRepo()
        use_case = GetConversationHistoryUseCase(conv_repo)
        with pytest.raises(ConversationNotFoundError):
            await use_case.execute(str(ConversationId()))


class TestRenameConversationUseCase:
    @pytest.mark.asyncio
    async def test_rename(self):
        from forge.application.conversation.rename_conversation import (
            RenameConversationRequest,
            RenameConversationUseCase,
        )

        conv_repo = FakeConversationRepo()
        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        conv = Conversation.create(project_id=project.id, title="Old Title")
        await conv_repo.save(conv)

        use_case = RenameConversationUseCase(conv_repo)
        result = await use_case.execute(
            RenameConversationRequest(
                conversation_id=str(conv.id),
                title="New Title",
            )
        )
        assert result.title == "New Title"


class TestDeleteConversationUseCase:
    @pytest.mark.asyncio
    async def test_delete(self):
        from forge.application.conversation.delete_conversation import (
            DeleteConversationUseCase,
        )

        conv_repo = FakeConversationRepo()
        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        conv = Conversation.create(project_id=project.id, title="To Delete")
        await conv_repo.save(conv)

        use_case = DeleteConversationUseCase(conv_repo)
        result = await use_case.execute(str(conv.id))
        assert result.deleted is True

        # Verify it's gone
        fetched = await conv_repo.get_by_id(conv.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        from forge.application.conversation.delete_conversation import (
            DeleteConversationUseCase,
        )

        conv_repo = FakeConversationRepo()
        use_case = DeleteConversationUseCase(conv_repo)
        with pytest.raises(ConversationNotFoundError):
            await use_case.execute(str(ConversationId()))


class TestListConversationsUseCase:
    @pytest.mark.asyncio
    async def test_list_conversations(self):
        from forge.application.conversation.list_conversations import (
            ListConversationsUseCase,
        )

        project_repo = FakeProjectRepo()
        conv_repo = FakeConversationRepo()

        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        await project_repo.save(project)

        for i in range(3):
            conv = Conversation.create(project_id=project.id, title=f"Conv {i}")
            await conv_repo.save(conv)

        use_case = ListConversationsUseCase(conv_repo, project_repo)
        result = await use_case.execute(str(project.id))
        assert result.total == 3
        assert len(result.conversations) == 3


class TestSearchConversationsUseCase:
    @pytest.mark.asyncio
    async def test_search_by_title(self):
        from forge.application.conversation.search_conversations import (
            SearchConversationsUseCase,
        )

        project_repo = FakeProjectRepo()
        conv_repo = FakeConversationRepo()

        project = Project.create(
            name="Test",
            description="D",
            stack=TechStack.from_list(["python"]),
        )
        await project_repo.save(project)

        conv = Conversation.create(project_id=project.id, title="Debug auth bug")
        await conv_repo.save(conv)

        use_case = SearchConversationsUseCase(conv_repo, project_repo)
        result = await use_case.execute(str(project.id), "auth")
        assert result.total == 1
        assert "auth" in result.conversations[0].title.lower()


class TestTokenManager:
    def test_estimate_tokens(self):
        from forge.application.conversation.token_manager import TokenManager

        tm = TokenManager()
        assert tm.estimate_tokens("hello") >= 1

    def test_build_context_window_small(self):
        from forge.application.conversation.token_manager import TokenManager

        tm = TokenManager(max_tokens=10000)
        conv = Conversation.create(project_id=ProjectId(), title="T")
        for i in range(5):
            conv.add_message(
                Message(
                    id=MessageId(),
                    conversation_id=str(conv.id),
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i}",
                    token_count=20,
                )
            )
        window = tm.build_context_window(conv)
        assert len(window.messages) == 5
        assert window.total_tokens > 0

    def test_build_context_window_with_summary(self):
        from forge.application.conversation.token_manager import TokenManager

        tm = TokenManager(max_tokens=200)
        conv = Conversation.create(project_id=ProjectId(), title="T")
        from forge.domain.conversation.entities.summary import ConversationSummary
        from forge.domain.conversation.value_objects import SummaryId

        conv.add_summary(
            ConversationSummary(
                id=SummaryId(),
                conversation_id=conv.id,
                content="This is a summary of the conversation",
                token_count=15,
            )
        )
        for i in range(20):
            conv.add_message(
                Message(
                    id=MessageId(),
                    conversation_id=str(conv.id),
                    role="user",
                    content=f"Message {i} with some content to make it longer",
                    token_count=50,
                )
            )
        window = tm.build_context_window(conv)
        # Should prune old messages to fit budget
        assert window.summary_tokens == 15
        assert len(window.messages) < 20

    def test_should_summarize(self):
        from forge.application.conversation.token_manager import TokenManager

        tm = TokenManager()
        conv = Conversation.create(project_id=ProjectId(), title="T")
        assert not tm.should_summarize(conv)
        for i in range(25):
            conv.add_message(
                Message(
                    id=MessageId(),
                    conversation_id=str(conv.id),
                    role="user",
                    content=f"msg {i}",
                )
            )
        assert tm.should_summarize(conv)


class TestContextBuilder:
    def test_build_basic(self):
        from forge.application.conversation.context_builder import ContextBuilder

        cb = ContextBuilder()
        conv = Conversation.create(project_id=ProjectId(), title="T")
        conv.add_message(Message.create_user(str(conv.id), "Hello", token_count=5))

        ctx = cb.build(conv, "What about this?", memory_context=None)
        assert ctx.user_message == "What about this?"
        assert len(ctx.history_messages) >= 1

    def test_build_with_memory(self):
        from forge.application.conversation.context_builder import ContextBuilder

        cb = ContextBuilder()
        conv = Conversation.create(project_id=ProjectId(), title="T")
        memory = {
            "relevant_code": [
                {"payload": {"name": "foo", "file_path": "foo.py"}, "score": 0.9},
            ],
            "relevant_decisions": [],
            "relevant_bugs": [],
        }
        ctx = cb.build(conv, "test", memory_context=memory)
        assert len(ctx.sources) == 1
        assert ctx.sources[0]["name"] == "foo"

    def test_build_with_summary(self):
        from forge.application.conversation.context_builder import ContextBuilder

        cb = ContextBuilder()
        conv = Conversation.create(project_id=ProjectId(), title="T")
        from forge.domain.conversation.entities.summary import ConversationSummary
        from forge.domain.conversation.value_objects import SummaryId

        conv.add_summary(
            ConversationSummary(
                id=SummaryId(),
                conversation_id=conv.id,
                content="Previous discussion about auth",
                token_count=20,
            )
        )
        conv.add_message(Message.create_user(str(conv.id), "Hello", token_count=5))

        ctx = cb.build(conv, "Continue", memory_context=None)
        # Should have summary in history
        assert any("summary" in m["content"].lower() for m in ctx.history_messages)
