import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from forge.application.conversation.send_conversation_message import SendConversationMessageUseCase, SendMessageRequest
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.value_objects.conversation_id import ConversationId

@pytest.fixture
def conversation_repo():
    class FakeConvRepo:
        def __init__(self):
            self.convs = {}
        async def save(self, conversation):
            self.convs[conversation.id] = conversation
        async def get_by_id(self, conv_id):
            return self.convs.get(conv_id)
    return FakeConvRepo()

@pytest.fixture
def llm_service():
    llm = MagicMock()
    llm.is_configured = True
    llm.chat = AsyncMock()
    return llm

@pytest.mark.asyncio
async def test_rel_conversation_state_llm_failure(conversation_repo, llm_service):
    """Property 2, 14, 17: Conversation Consistency and Job Cancellation."""
    
    # 1. Setup the usecase
    usecase = SendConversationMessageUseCase(
        conversation_repo=conversation_repo,
        context_retriever=AsyncMock(return_value=None),
        llm_service=llm_service,
    )
    
    # 2. Setup initial conversation state
    conv = Conversation.create(project_id="test-proj", title="Test")
    await conversation_repo.save(conv)
    
    request = SendMessageRequest(
        conversation_id=str(conv.id),
        message="Hello World"
    )
    
    # 3. Simulate an LLM failure
    llm_service.chat.side_effect = TimeoutError("LLM Timed out")
    
    with pytest.raises(TimeoutError):
        await usecase.execute(request)
        
    # 4. Assertions on the resulting state
    # We want to ensure the conversation state didn't become corrupt or partially complete
    # The user message should ideally be present, or neither if it's atomic.
    # Currently, Forge saves the user message before calling the LLM. 
    # Let's verify that the user message is saved and there's no assistant message.
    
    persisted_conv = await conversation_repo.get_by_id(conv.id)
    
    assert persisted_conv is not None
    assert len(persisted_conv.messages) == 1, "Only the user message should be persisted"
    assert persisted_conv.messages[0].role == "user"
    assert persisted_conv.messages[0].content == "Hello World"
