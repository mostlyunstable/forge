import pytest
import json
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.domain.agent.agent_profile import AgentProfile
from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider

class FailingLLM(ILLMProvider):
    async def chat(self, *args, **kwargs):
        raise Exception("API Rate Limit Exceeded")
        
    async def chat_stream(self, *args, **kwargs):
        raise Exception("API Connection Dropped")

class InfiniteToolLLM(ILLMProvider):
    def __init__(self):
        self.iterations = 0
        
    async def chat(self, *args, **kwargs):
        class MockResponse:
            tool_calls = [{"id": "call_123", "function": {"name": "run_shell_command", "arguments": '{"command": "echo loop"}'}}]
            content = ""
        return MockResponse()
        
    async def chat_stream(self, *args, **kwargs):
        self.iterations += 1
        class MockChunk:
            tool_calls = [{"function": {"name": "run_shell_command", "arguments": '{"command": "echo loop"}'}}]
            content = ""
        yield MockChunk()


@pytest.mark.asyncio
async def test_adversarial_engine_api_failure():
    """
    Test if the ReasoningEngine emits a terminal ERROR state upon LLM API failure
    rather than just crashing or hanging.
    """
    profile = AgentProfile(name="bot1", role="Role1", system_prompt_template="Test", allowed_tools=[])
    engine = ReasoningEngine(FailingLLM(), agent_profile=profile)
    
    cw = ContextWindow(summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=4000)
    
    chunks = []
    
    try:
        async for chunk in engine.generate_response_stream(cw, "context", "prompt"):
            chunks.append(chunk)
    except Exception:
        pass # We want to see what was emitted before crash
        
    # Verify that the last chunk is an error type or at least the engine doesn't crash the loop
    # In Cycle 1, we expect the exception to just crash the stream since there's no catch-all error handling inside generate_response_stream.
    
    terminal_emitted = False
    for c in chunks:
        if c.get("type") == "error":
            terminal_emitted = True
            
    assert terminal_emitted, "Agent loop failed to emit a terminal ERROR state on API crash, resulting in a silent hang/crash for the user."

@pytest.mark.asyncio
async def test_adversarial_engine_infinite_tool_loop():
    """
    Test if the ReasoningEngine enforces max_iterations and terminates with an error 
    if the LLM just keeps calling tools infinitely.
    """
    profile = AgentProfile(name="bot1", role="Role1", system_prompt_template="Test", allowed_tools=["run_shell_command"])
    engine = ReasoningEngine(InfiniteToolLLM(), agent_profile=profile)
    
    cw = ContextWindow(summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=4000)
    
    chunks = []
    async for chunk in engine.generate_response_stream(cw, "context", "prompt"):
        chunks.append(chunk)
        
    # The loop should terminate after max_iterations (default 10)
    # and the last message should indicate the iteration budget was exceeded.
    budget_exceeded = False
    for c in chunks:
        if c.get("type") == "error" and "maximum iterations" in c.get("message", ""):
            budget_exceeded = True
            
    assert budget_exceeded, "Agent loop failed to terminate a runaway LLM calling tools infinitely."
