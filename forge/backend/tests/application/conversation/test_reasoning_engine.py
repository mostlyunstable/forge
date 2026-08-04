from unittest.mock import AsyncMock, MagicMock

import pytest

from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider
from forge.infrastructure.llm.llm_service import LLMResponse


class MockLLMProvider(ILLMProvider):
    def __init__(self):
        self.chat_mock = AsyncMock()

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        return await self.chat_mock(messages, **kwargs)

    async def chat_stream(self, messages: list[dict[str, str]], **kwargs):
        yield {"type": "text", "content": "Streamed text"}


@pytest.fixture
def mock_llm_provider():
    return MockLLMProvider()


@pytest.fixture
def reasoning_engine(mock_llm_provider):
    return ReasoningEngine(mock_llm_provider)


@pytest.mark.asyncio
async def test_reasoning_engine_injects_system_prompt_with_context(
    reasoning_engine, mock_llm_provider
):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="Response based on context.", model="test", usage={}
    )
    context_window = ContextWindow(
        summary="Previous summary",
        summary_tokens=10,
        messages=[],
        message_tokens=0,
        total_tokens=10,
    )
    retrieved_context = "This is a piece of evidence."
    user_prompt = "What is the evidence?"

    # Act
    response = await reasoning_engine.generate_response(
        context_window=context_window, retrieved_context=retrieved_context, user_prompt=user_prompt
    )

    # Assert
    assert response == "Response based on context."
    mock_llm_provider.chat_mock.assert_called_once()
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]

    assert len(called_messages) == 2
    assert called_messages[0]["role"] == "system"
    assert "You are **Forge**" in called_messages[0]["content"]
    assert "## Retrieved Context\nThis is a piece of evidence." in called_messages[0]["content"]
    assert "Conversation Summary:\nPrevious summary" in called_messages[0]["content"]
    assert called_messages[1]["role"] == "user"
    assert called_messages[1]["content"] == user_prompt


@pytest.mark.asyncio
async def test_reasoning_engine_handles_empty_context(reasoning_engine, mock_llm_provider):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="I am uncertain because the evidence is missing.", model="test", usage={}
    )
    context_window = ContextWindow(
        summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=0
    )
    retrieved_context = ""
    user_prompt = "Tell me about X."

    # Act
    response = await reasoning_engine.generate_response(
        context_window=context_window, retrieved_context=retrieved_context, user_prompt=user_prompt
    )

    # Assert
    assert response == "I am uncertain because the evidence is missing."
    mock_llm_provider.chat_mock.assert_called_once()
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]

    assert len(called_messages) == 2
    assert called_messages[0]["role"] == "system"
    assert "You are **Forge**" in called_messages[0]["content"]


@pytest.mark.asyncio
async def test_reasoning_engine_includes_history_messages(reasoning_engine, mock_llm_provider):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="Success", model="test", usage={}
    )

    # Mocking messages
    msg1 = MagicMock()
    msg1.role = "user"
    msg1.content = "Hi"
    msg1.metadata = {}

    msg2 = MagicMock()
    msg2.role = "assistant"
    msg2.content = "Hello"
    msg2.metadata = {}

    context_window = ContextWindow(
        summary="", summary_tokens=0, messages=[msg1, msg2], message_tokens=2, total_tokens=2
    )

    # Act
    await reasoning_engine.generate_response(
        context_window=context_window, retrieved_context="Context info", user_prompt="New question"
    )

    # Assert
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]
    assert len(called_messages) == 4
    assert called_messages[0]["role"] == "system"
    assert called_messages[1]["role"] == "user"
    assert called_messages[1]["content"] == "Hi"
    assert called_messages[2]["role"] == "assistant"
    assert called_messages[2]["content"] == "Hello"
    assert called_messages[3]["role"] == "user"
    assert called_messages[3]["content"] == "New question"
