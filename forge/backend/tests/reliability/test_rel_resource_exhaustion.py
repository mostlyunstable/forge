import pytest

from forge.application.conversation.context_builder import ContextBuilder
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects import ConversationId
from forge.domain.projects.value_objects.project_id import ProjectId

def test_rel_resource_exhaustion_context_builder():
    """Property 19: Context Window Overflow.
    
    If conversation history and memory retrieval return massive amounts of text,
    the ContextBuilder must truncate them to fit within the token budget.
    """
    builder = ContextBuilder()
    conv_id = ConversationId()
    conversation = Conversation.create(project_id=ProjectId(), title="Test")
    
    # Add 100 huge messages
    for i in range(100):
        msg = Message.create_user(
            conversation_id=conv_id,
            content="huge " * 1000, # 1000 words ~ 1000 tokens each
            token_count=1000
        )
        conversation.add_message(msg)
        
    memory_context = {
        "relevant_code": [
            {"payload": {"name": f"func_{i}", "file_path": f"file_{i}.py"}, "score": 0.9} 
            for i in range(100)
        ]
    }
    
    # Should restrict history to max_history_tokens, and memory to top 5
    llm_context = builder.build(
        conversation=conversation,
        user_message="test",
        memory_context=memory_context,
        max_history_tokens=5000
    )
    
    # History messages: each message is 1000 tokens. Budget 5000 -> max 5 history messages
    assert len(llm_context.history_messages) <= 6 # 5 messages + memory system prompts
    
    # Memory should be truncated to top 5
    system_messages = [m for m in llm_context.history_messages if m["role"] == "system"]
    assert any("func_4 in file_4.py" in m["content"] for m in system_messages)
    assert not any("func_10 in file_10.py" in m["content"] for m in system_messages)

