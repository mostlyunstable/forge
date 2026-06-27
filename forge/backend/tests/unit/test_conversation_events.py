"""Unit tests for Conversation domain events."""
from forge.domain.conversation.events import (
    ConversationCreated,
    MessageAdded,
    ConversationRenamed,
    ConversationDeleted,
    ConversationSummarized,
)


def test_conversation_created():
    event = ConversationCreated(
        conversation_id="c1",
        project_id="p1",
        title="Test",
    )
    assert event.event_type == "conversation.created"
    d = event.to_dict()
    assert d["conversation_id"] == "c1"
    assert d["project_id"] == "p1"
    assert d["title"] == "Test"


def test_message_added():
    event = MessageAdded(
        conversation_id="c1",
        role="user",
        token_count=42,
    )
    assert event.event_type == "conversation.message_added"
    d = event.to_dict()
    assert d["role"] == "user"
    assert d["token_count"] == 42


def test_conversation_renamed():
    event = ConversationRenamed(
        conversation_id="c1",
        new_title="New Title",
    )
    assert event.event_type == "conversation.renamed"
    d = event.to_dict()
    assert d["new_title"] == "New Title"


def test_conversation_deleted():
    event = ConversationDeleted(conversation_id="c1")
    assert event.event_type == "conversation.deleted"
    d = event.to_dict()
    assert d["conversation_id"] == "c1"


def test_conversation_summarized():
    event = ConversationSummarized(
        conversation_id="c1",
        message_count_pruned=15,
    )
    assert event.event_type == "conversation.summarized"
    d = event.to_dict()
    assert d["message_count_pruned"] == 15
