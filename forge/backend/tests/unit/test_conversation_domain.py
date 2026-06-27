"""Unit tests for Conversation domain entities."""
import pytest
from uuid import uuid4

from forge.domain.conversation.entities.conversation import Conversation, AUTO_SUMMARIZE_THRESHOLD
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.value_objects.message_id import MessageId
from forge.domain.projects.value_objects.project_id import ProjectId


class TestConversationId:
    def test_create_generates_uuid(self):
        cid = ConversationId()
        assert cid.value is not None

    def test_from_string(self):
        raw = str(uuid4())
        cid = ConversationId.from_string(raw)
        assert str(cid.value) == raw

    def test_str(self):
        cid = ConversationId()
        assert str(cid) == str(cid.value)


class TestMessageId:
    def test_create_generates_uuid(self):
        mid = MessageId()
        assert mid.value is not None

    def test_from_string(self):
        raw = str(uuid4())
        mid = MessageId.from_string(raw)
        assert str(mid.value) == raw


class TestMessage:
    def test_create_user(self):
        msg = Message.create_user("conv-123", "Hello", token_count=5)
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.conversation_id == "conv-123"
        assert msg.token_count == 5

    def test_create_assistant(self):
        msg = Message.create_assistant("conv-123", "Hi there", token_count=3)
        assert msg.role == "assistant"
        assert msg.content == "Hi there"

    def test_create_system(self):
        msg = Message.create_system("conv-123", "System message")
        assert msg.role == "system"

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError, match="Invalid role"):
            Message(
                id=MessageId(),
                conversation_id="conv-1",
                role="invalid",
                content="test",
            )

    def test_default_timestamp(self):
        msg = Message.create_user("conv-1", "test")
        assert msg.created_at is not None


class TestConversation:
    def test_create(self):
        pid = ProjectId()
        conv = Conversation.create(project_id=pid, title="Test")
        assert conv.title == "Test"
        assert conv.project_id == pid
        assert conv.message_count == 0
        assert conv.messages == []

    def test_add_message(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        msg = Message.create_user(str(conv.id), "Hello", token_count=10)
        conv.add_message(msg)
        assert conv.message_count == 1
        assert conv.total_token_count == 10
        assert len(conv.messages) == 1

    def test_add_multiple_messages(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        for i in range(5):
            role = "user" if i % 2 == 0 else "assistant"
            msg = Message(id=MessageId(), role=role, conversation_id=str(conv.id), content=f"msg-{i}", token_count=10)
            conv.add_message(msg)
        assert conv.message_count == 5
        assert conv.total_token_count == 50

    def test_needs_summarize(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        assert not conv.needs_summarize()
        for i in range(AUTO_SUMMARIZE_THRESHOLD + 1):
            conv.add_message(Message(
                id=MessageId(),
                conversation_id=str(conv.id),
                role="user",
                content=f"msg-{i}",
            ))
        assert conv.needs_summarize()

    def test_set_summary(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        conv.set_summary("Summary text", token_count=50)
        assert conv.summary == "Summary text"
        assert conv.summary_token_count == 50

    def test_rename(self):
        conv = Conversation.create(project_id=ProjectId(), title="Old")
        conv.rename("New Title")
        assert conv.title == "New Title"

    def test_recent_messages(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        for i in range(25):
            conv.add_message(Message(
                id=MessageId(),
                conversation_id=str(conv.id),
                role="user",
                content=f"msg-{i}",
            ))
        recent = conv.recent_messages
        assert len(recent) == 20
        assert recent[0].content == "msg-5"
        assert recent[-1].content == "msg-24"

    def test_summary_combined(self):
        conv = Conversation.create(project_id=ProjectId(), title="T")
        conv.set_summary("Old summary", 10)
        conv.set_summary("New summary", 20)
        assert conv.summary == "New summary"
