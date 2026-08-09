import pytest
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from forge.application.agent.swarm_orchestrator import SwarmOrchestrator
from forge.application.conversation.token_manager import ContextWindow

@pytest.fixture
def mock_llm_provider():
    llm = AsyncMock()
    # Mock stream response
    async def mock_stream(*args, **kwargs):
        yield {"type": "text", "content": "Hello"}
    llm.generate_stream = mock_stream
    llm.generate = AsyncMock(return_value="Delegated result")
    return llm

@pytest.fixture
def mock_registry():
    registry = MagicMock()
    # Mock get
    def mock_get(name):
        if name == "unknown_agent":
            return None
        profile = MagicMock()
        profile.role = name
        return profile
    registry.get.side_effect = mock_get
    return registry

@pytest.fixture
def context_window():
    return ContextWindow(
        summary="",
        summary_tokens=0,
        messages=[],
        message_tokens=0,
        total_tokens=4096
    )

@pytest.mark.asyncio
async def test_swarm_single_agent_success(mock_llm_provider, mock_registry, context_window):
    orchestrator = SwarmOrchestrator(mock_llm_provider, mock_registry)
    
    chunks = []
    async for chunk in orchestrator.execute_task(
        agent_name="test_agent",
        context_window=context_window,
        retrieved_context="Test context",
        user_prompt="Do something"
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert chunks[0]["type"] == "status"
    assert "test_agent" in chunks[0]["message"]
    # Check that stream from LLM was yielded (which might be wrapped by ReasoningEngine, 
    # but at least we get some chunks out)

@pytest.mark.asyncio
async def test_swarm_unknown_agent_error(mock_llm_provider, mock_registry, context_window):
    orchestrator = SwarmOrchestrator(mock_llm_provider, mock_registry)
    
    chunks = []
    async for chunk in orchestrator.execute_task(
        agent_name="unknown_agent",
        context_window=context_window,
        retrieved_context="Test context"
    ):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0]["type"] == "status"
    assert "not found" in chunks[0]["message"]

@pytest.mark.asyncio
async def test_swarm_delegation_success(mock_llm_provider, mock_registry, context_window, monkeypatch):
    orchestrator = SwarmOrchestrator(mock_llm_provider, mock_registry)
    
    # We need to simulate the engine invoking the tool_callback.
    # We can patch ReasoningEngine to invoke the callback instead of generating a stream.
    from forge.application.conversation.reasoning_engine import ReasoningEngine
    
    original_init = ReasoningEngine.__init__
    
    async def fake_generate_response_stream(self, *args, **kwargs):
        # Invoke the callback
        if self._tool_executor_callback:
            result = await self._tool_executor_callback("delegate_task", {"agent_name": "child_agent", "task": "child task"})
            yield {"type": "text", "content": result}
        else:
            yield {"type": "text", "content": "no callback"}
            
    monkeypatch.setattr(ReasoningEngine, "generate_response_stream", fake_generate_response_stream)
    
    async def fake_generate_response(self, *args, **kwargs):
        return "Child completed task."
        
    monkeypatch.setattr(ReasoningEngine, "generate_response", fake_generate_response)

    chunks = []
    async for chunk in orchestrator.execute_task(
        agent_name="parent_agent",
        context_window=context_window,
        retrieved_context="Test context"
    ):
        chunks.append(chunk)

    # First is status
    assert chunks[0]["type"] == "status"
    # Second is the mocked stream output from our fake_generate_response_stream
    assert chunks[1]["type"] == "text"
    assert "Child completed task." in chunks[1]["content"]


@pytest.mark.asyncio
async def test_swarm_max_depth_exceeded(mock_llm_provider, mock_registry, context_window, monkeypatch):
    orchestrator = SwarmOrchestrator(mock_llm_provider, mock_registry)
    
    from forge.application.conversation.reasoning_engine import ReasoningEngine
    
    async def fake_generate_response_stream(self, *args, **kwargs):
        if self._tool_executor_callback:
            result = await self._tool_executor_callback("delegate_task", {"agent_name": "child_agent", "task": "child task"})
            yield {"type": "text", "content": result}
            
    monkeypatch.setattr(ReasoningEngine, "generate_response_stream", fake_generate_response_stream)
    
    async def fake_generate_response(self, *args, **kwargs):
        # Child also tries to delegate!
        if self._tool_executor_callback:
            result = await self._tool_executor_callback("delegate_task", {"agent_name": "grandchild_agent", "task": "grandchild task"})
            return result
        return "Should not reach here"
        
    monkeypatch.setattr(ReasoningEngine, "generate_response", fake_generate_response)

    chunks = []
    async for chunk in orchestrator.execute_task(
        agent_name="parent_agent",
        context_window=context_window,
        retrieved_context="Test context",
        max_depth=2
    ):
        chunks.append(chunk)
        
    assert chunks[0]["type"] == "status"
    assert chunks[1]["type"] == "text"
    # Parent delegates to child (depth 1 -> 2). 
    # Child delegates to grandchild (depth 2 >= max_depth 2, so it fails).
    assert "Max delegation depth exceeded." in chunks[1]["content"]

