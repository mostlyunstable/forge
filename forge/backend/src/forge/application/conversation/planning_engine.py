from typing import Any

from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider


class PlanningEngine:
    """
    Planning layer that generates structured plans based on a user query and the conversation context.
    Enforces read-only constraints: generates recommendations strictly without executing changes.
    """

    def __init__(self, llm_provider: ILLMProvider):
        self._llm = llm_provider

    async def generate_plan(
        self, query: str, context_window: ContextWindow, retrieved_context: str = "", **kwargs: Any
    ) -> str:
        """
        Generate a structured plan based on the user query, context window, and retrieved context.

        Args:
            query: The user query (e.g., "plan a migration to postgres").
            context_window: The conversation history and summary.
            retrieved_context: Grounding context retrieved from search/memory.
            **kwargs: Extra parameters for the LLM.

        Returns:
            The LLM response containing the structured plan.
        """
        system_prompt = (
            "You are an AI planning assistant. Your purpose is to generate structured plans based on the user's query.\n"
            "You MUST provide recommendations strictly based on retrieved evidence.\n"
            "You MUST operate under strict read-only constraints: you NEVER modify repositories, "
            "generate commits, or execute changes automatically. You only output text recommendations.\n"
            "Your output should be a structured plan that may include, but is not limited to: "
            "implementation steps, debugging strategies, migration planning, testing plans, "
            "architecture comparisons, and refactoring recommendations.\n\n"
            f"Retrieved Context:\n{retrieved_context}\n"
        )

        if context_window.summary:
            system_prompt += f"\nConversation Summary:\n{context_window.summary}\n"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for msg in context_window.messages:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": query})

        response = await self._llm.chat(messages, **kwargs)
        return response.content or ""
