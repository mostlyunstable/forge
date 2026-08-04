from unittest.mock import AsyncMock, MagicMock

import pytest

from forge.application.conversation.planning_engine import PlanningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider
from forge.infrastructure.llm.llm_service import LLMResponse


class MockLLMProvider(ILLMProvider):
    def __init__(self):
        self.chat_mock = AsyncMock()

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        return await self.chat_mock(messages, **kwargs)

    async def chat_stream(self, messages: list[dict[str, str]], **kwargs):
        yield {"type": "text", "content": "Streamed plan"}


@pytest.fixture
def mock_llm_provider():
    return MockLLMProvider()


@pytest.fixture
def planning_engine(mock_llm_provider):
    return PlanningEngine(mock_llm_provider)


@pytest.mark.asyncio
async def test_planning_engine_injects_system_prompt_with_read_only_constraints(
    planning_engine, mock_llm_provider
):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="Structured Plan", model="test", usage={}
    )
    context_window = ContextWindow(
        summary="Previous summary",
        summary_tokens=10,
        messages=[],
        message_tokens=0,
        total_tokens=10,
    )
    retrieved_context = "This is a piece of evidence for planning."
    query = "plan a migration to postgres"

    # Act
    response = await planning_engine.generate_plan(
        query=query, context_window=context_window, retrieved_context=retrieved_context
    )

    # Assert
    assert response == "Structured Plan"
    mock_llm_provider.chat_mock.assert_called_once()
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]

    assert len(called_messages) == 2
    assert called_messages[0]["role"] == "system"
    assert "You MUST operate under strict read-only constraints" in called_messages[0]["content"]
    assert (
        "you NEVER modify repositories, generate commits, or execute changes automatically"
        in called_messages[0]["content"]
    )
    assert (
        "You MUST provide recommendations strictly based on retrieved evidence."
        in called_messages[0]["content"]
    )
    assert (
        "Retrieved Context:\nThis is a piece of evidence for planning."
        in called_messages[0]["content"]
    )
    assert "Conversation Summary:\nPrevious summary" in called_messages[0]["content"]

    assert called_messages[1]["role"] == "user"
    assert called_messages[1]["content"] == query


@pytest.mark.asyncio
async def test_planning_engine_includes_history_messages(planning_engine, mock_llm_provider):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="Plan with history", model="test", usage={}
    )

    # Mocking messages
    msg1 = MagicMock()
    msg1.role = "user"
    msg1.content = "What database?"
    msg1.metadata = {}

    msg2 = MagicMock()
    msg2.role = "assistant"
    msg2.content = "Postgres"
    msg2.metadata = {}

    context_window = ContextWindow(
        summary="", summary_tokens=0, messages=[msg1, msg2], message_tokens=2, total_tokens=2
    )

    # Act
    await planning_engine.generate_plan(
        query="plan migration", context_window=context_window, retrieved_context="Context info"
    )

    # Assert
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]
    assert len(called_messages) == 4
    assert called_messages[0]["role"] == "system"
    assert called_messages[1]["role"] == "user"
    assert called_messages[1]["content"] == "What database?"
    assert called_messages[2]["role"] == "assistant"
    assert called_messages[2]["content"] == "Postgres"
    assert called_messages[3]["role"] == "user"
    assert called_messages[3]["content"] == "plan migration"


@pytest.mark.asyncio
async def test_planning_engine_verifies_output_format_instructions(
    planning_engine, mock_llm_provider
):
    # Arrange
    mock_llm_provider.chat_mock.return_value = LLMResponse(
        content="Plan step 1", model="test", usage={}
    )
    context_window = ContextWindow(
        summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=0
    )

    # Act
    await planning_engine.generate_plan(query="test query", context_window=context_window)

    # Assert
    called_messages = mock_llm_provider.chat_mock.call_args[0][0]
    system_prompt = called_messages[0]["content"]
    assert "structured plan that may include" in system_prompt
    assert (
        "implementation steps, debugging strategies, migration planning, testing plans, architecture comparisons, and refactoring recommendations"
        in system_prompt
    )
