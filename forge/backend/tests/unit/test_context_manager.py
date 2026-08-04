from uuid import UUID

import pytest

from forge.application.conversation.context_manager import (
    ConversationContextManager,
    RetrievedContext,
)
from forge.application.conversation.token_manager import TokenManager
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import ConversationMessage
from forge.domain.conversation.entities.summary import ConversationSummary
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.projects.value_objects.project_id import ProjectId


class MockConversationRepo:
    def __init__(self, conversation):
        self.conversation = conversation

    async def get_by_id(self, conv_id):
        return self.conversation

    async def get_by_project(self, project_id, skip=0, limit=50):
        return [self.conversation]

    async def save(self, conv):
        return conv

    async def delete(self, conv_id):
        return True

    async def search(self, project_id, query):
        return []

    async def count_by_project(self, project_id):
        return 1


@pytest.mark.asyncio
async def test_context_manager_build():
    conv_id = ConversationId()
    project_id = ProjectId(UUID("00000000-0000-0000-0000-000000000000"))
    conv = Conversation.create(project_id, "Test Conv")

    msg1 = ConversationMessage.create_user(conv_id, content="Hello", token_count=10)
    msg2 = ConversationMessage.create_assistant(conv_id, content="Hi there", token_count=10)
    conv.add_message(msg1)
    conv.add_message(msg2)

    summary = ConversationSummary.create(conv_id, content="A summary", token_count=10)
    conv.add_summary(summary)

    repo = MockConversationRepo(conv)
    token_manager = TokenManager(max_tokens=100)

    manager = ConversationContextManager(conversation_repo=repo, token_manager=token_manager)

    retrieved = [
        RetrievedContext(source="memory", content="Memory chunk 1", score=0.9),
        RetrievedContext(source="graph", content="Graph chunk 1", score=0.8),
        RetrievedContext(source="memory", content="Memory chunk 1", score=0.9),  # duplicate
    ]

    context = await manager.build_context(conv_id, retrieved)

    assert context is not None
    assert "A summary" in context["summary"]
    # memory chunk 1 should be deduplicated
    memory_chunks = [c for c in context["retrieved"] if c["source"] == "memory"]
    assert len(memory_chunks) == 1
    assert memory_chunks[0]["content"] == "Memory chunk 1"

    # check compression
    assert len(context["messages"]) <= 2


@pytest.mark.asyncio
async def test_context_manager_compression():
    conv_id = ConversationId()
    project_id = ProjectId(UUID("00000000-0000-0000-0000-000000000000"))
    conv = Conversation.create(project_id, "Test Conv")

    # Each message is ~10 tokens
    # Total token budget is 30, retrieved contexts take ~10. Left budget = 20.
    # Summary takes 10 tokens. Left budget = 10.
    # Therefore only the last message should fit.
    msg1 = ConversationMessage.create_user(
        conv_id, content="First very long user message here", token_count=10
    )
    msg2 = ConversationMessage.create_assistant(
        conv_id, content="Assistant reply to the first message", token_count=10
    )
    msg3 = ConversationMessage.create_user(
        conv_id, content="Second user message here", token_count=10
    )
    conv.add_message(msg1)
    conv.add_message(msg2)
    conv.add_message(msg3)

    summary = ConversationSummary.create(
        conv_id, content="Summary of the conversation", token_count=10
    )
    conv.add_summary(summary)

    repo = MockConversationRepo(conv)
    token_manager = TokenManager(max_tokens=30)
    manager = ConversationContextManager(conversation_repo=repo, token_manager=token_manager)

    retrieved = [
        RetrievedContext(source="memory", content="Short context", score=1.0),
    ]

    context = await manager.build_context(conv_id, retrieved)

    # Context window tokens: memory ~3 tokens (len("Short context")//4 = 3).
    # Tokens budget = 30.
    # memory = 3
    # available for msgs + summary = 27.
    # summary = 10.
    # available for msgs = 17.
    # msg3 = 10 -> fits.
    # msg2 = 10 -> exceeds (10 + 10 > 17).
    # Only msg3 should be included.
    assert len(context["messages"]) == 1
    assert context["messages"][0]["content"] == "Second user message here"
