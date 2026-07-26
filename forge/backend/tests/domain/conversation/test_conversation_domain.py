import pytest
from datetime import datetime, timezone

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import ConversationMessage
from forge.domain.conversation.entities.session import ConversationSession
from forge.domain.conversation.entities.summary import ConversationSummary
from forge.domain.conversation.entities.citation import ConversationCitation
from forge.domain.conversation.value_objects import (
    ConversationId,
    MessageId,
    ConversationState,
    SessionId,
    SummaryId,
    CitationId
)

def test_create_conversation():
    project_id = ProjectId()
    conv = Conversation.create(project_id, "Test Conversation")
    assert conv.title == "Test Conversation"
    assert conv.project_id == project_id
    assert conv.state == ConversationState.ACTIVE
    assert len(conv.messages) == 0

def test_add_message():
    conv = Conversation.create(ProjectId(), "Test")
    msg = ConversationMessage.create_user(conv.id, "Hello", 10)
    conv.add_message(msg)
    
    assert len(conv.messages) == 1
    assert conv.total_token_count == 10
    assert conv.state == ConversationState.ACTIVE

def test_message_citation():
    conv = Conversation.create(ProjectId(), "Test")
    msg = ConversationMessage.create_user(conv.id, "Hello", 10)
    citation = ConversationCitation.create(msg.id, "doc", "http://example.com", "snippet")
    msg.add_citation(citation)
    
    assert len(msg.citations) == 1
    assert msg.citations[0].source_reference == "http://example.com"
    assert msg.citations[0].source_type == "doc"

def test_session_management():
    conv = Conversation.create(ProjectId(), "Test")
    session1 = conv.start_session()
    
    assert session1.is_active is True
    assert conv.active_session == session1
    
    session2 = conv.start_session()
    assert session1.is_active is False  # Starting a new session ends the previous one
    assert session2.is_active is True
    assert conv.active_session == session2
    
    conv.end_active_session()
    assert session2.is_active is False
    assert conv.active_session is None
    assert conv.state == ConversationState.IDLE

def test_summarization():
    conv = Conversation.create(ProjectId(), "Test")
    summary = ConversationSummary.create(conv.id, "This is a summary", 5)
    conv.add_summary(summary)
    
    assert len(conv.summaries) == 1
    assert conv.state == ConversationState.SUMMARIZED

def test_archiving():
    conv = Conversation.create(ProjectId(), "Test")
    conv.start_session()
    conv.archive()
    
    assert conv.state == ConversationState.ARCHIVED
    assert conv.active_session is None
    
    # Cannot add message to archived conversation
    with pytest.raises(ValueError):
        msg = ConversationMessage.create_user(conv.id, "Hello", 10)
        conv.add_message(msg)
        
    # Cannot start session in archived conversation
    with pytest.raises(ValueError):
        conv.start_session()
        
    # Cannot summarize an archived conversation
    with pytest.raises(ValueError):
        summary = ConversationSummary.create(conv.id, "Summary", 5)
        conv.add_summary(summary)

def test_mark_idle():
    conv = Conversation.create(ProjectId(), "Test")
    conv.start_session()
    conv.mark_idle()
    
    assert conv.state == ConversationState.IDLE
    assert conv.active_session is None
