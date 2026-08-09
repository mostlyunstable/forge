import pytest
import os
import shutil
from forge.application.agent.tools import set_tools_base_dir, ForgeTools
from forge.domain.agent.agent_registry import AgentRegistry
from forge.application.agent.swarm_orchestrator import SwarmOrchestrator
from forge.infrastructure.llm.llm_service import LLMService
from forge.config.settings import Settings

@pytest.fixture
def rule_env(tmp_path):
    project_a = tmp_path / "project_a"
    project_b = tmp_path / "project_b"
    project_a.mkdir()
    project_b.mkdir()
    yield project_a, project_b

def test_adversarial_rule_isolation(rule_env):
    """
    Test if rules learned in Project A leak into Project B.
    """
    project_a, project_b = rule_env
    
    # Context A learns a rule
    set_tools_base_dir(project_a)
    ForgeTools.execute_tool("learn_rule", {"rule": "Always use spaces for indentation"})
    
    # Verify it exists in A
    rules_a = (project_a / ".forge_rules.md").read_text()
    assert "Always use spaces" in rules_a
    
    # Context B learns a different rule
    set_tools_base_dir(project_b)
    ForgeTools.execute_tool("learn_rule", {"rule": "Never use tabs"})
    
    # Verify B's rules
    rules_b = (project_b / ".forge_rules.md").read_text()
    
    # Vulnerability check: Did rule A bleed into rule B because of some global cache or state?
    assert "Always use spaces" not in rules_b, "Rule Isolation Bypass: Project B learned Project A's rule!"

@pytest.mark.asyncio
async def test_adversarial_swarm_exhaustion():
    """
    Test if the Swarm Orchestrator protects against deep delegation loops.
    """
    from forge.domain.agent.agent_profile import AgentProfile
    
    class DummyLLM:
        async def generate(self, *args, **kwargs):
            return None
            
        def generate_stream(self, *args, **kwargs):
            pass

    registry = AgentRegistry()
    registry.register(AgentProfile(name="bot1", role="Role1", system_prompt_template="Test", allowed_tools=[]))
    registry.register(AgentProfile(name="bot2", role="Role2", system_prompt_template="Test", allowed_tools=[]))

    orchestrator = SwarmOrchestrator(DummyLLM(), registry)
    
    # Call execute_task
    # Max depth is checked. We'll simulate a tool call.
    from forge.application.conversation.token_manager import ContextWindow
    
    # This is a bit tricky to mock without full context, but we can just see if the SwarmOrchestrator handles max_depth=0
    
    gen = orchestrator.execute_task(
        "bot1", 
        ContextWindow(summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=4000),
        "Context",
        max_depth=0
    )
    
    results = [chunk async for chunk in gen]
    
    # Expectation: It should refuse to execute at depth 0.
    assert len(results) == 1
    assert "Max delegation depth exceeded" in results[0]["message"], "Swarm failed to protect against depth exhaustion."
