from collections.abc import AsyncGenerator
from typing import Any

from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider
from forge.domain.agent.agent_registry import AgentRegistry


class SwarmOrchestrator:
    """
    Manages the lifecycle of multiple ReasoningEngine instances, allowing
    them to delegate tasks to one another.
    """

    def __init__(self, llm_provider: ILLMProvider, registry: AgentRegistry):
        self._llm = llm_provider
        self._registry = registry

    async def execute_task(
        self,
        agent_name: str,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        max_depth: int = 3,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:

        profile = self._registry.get(agent_name)
        if not profile:
            yield {"type": "status", "message": f"Error: Agent '{agent_name}' not found."}
            return

        if max_depth <= 0:
            yield {"type": "status", "message": "Error: Max delegation depth exceeded."}
            return

        yield {"type": "status", "message": f"🤖 [{profile.role}] taking over..."}

        def create_callback(current_depth: int):
            async def tool_callback(name: str, args: dict[str, Any]) -> str | None:
                if name == "delegate_task":
                    target_agent = args.get("agent_name", "")
                    task = args.get("task", "")

                    if current_depth >= max_depth:
                        return "Delegation failed: Max delegation depth exceeded."

                    child_cw = ContextWindow(
                        summary="",
                        summary_tokens=0,
                        messages=[],
                        message_tokens=0,
                        total_tokens=4096
                    )

                    child_profile = self._registry.get(target_agent)
                    if not child_profile:
                        return f"Delegation failed: Agent '{target_agent}' not found."

                    child_engine = ReasoningEngine(
                        self._llm, 
                        agent_profile=child_profile,
                        tool_executor_callback=create_callback(current_depth + 1)
                    )
                    
                    result = await child_engine.generate_response(
                        context_window=child_cw,
                        retrieved_context="Delegated task context.",
                        user_prompt=task,
                        **kwargs
                    )

                    return f"Task completed by {target_agent}.\nResult:\n{result}"

                return None

            return tool_callback

        engine = ReasoningEngine(
            self._llm,
            agent_profile=profile,
            tool_executor_callback=create_callback(1)
        )

        async for chunk in engine.generate_response_stream(
            context_window=context_window,
            retrieved_context=retrieved_context,
            user_prompt=user_prompt,
            **kwargs
        ):
            yield chunk
