from typing import Any
from forge.application.ports.llm_provider import ILLMProvider
from forge.application.conversation.token_manager import ContextWindow


class ReasoningEngine:
    """
    Reasoning layer that formats the ContextWindow, injects system prompts enforcing
    grounding and citation rules, and calls the ILLMProvider.
    """

    def __init__(self, llm_provider: ILLMProvider):
        self._llm = llm_provider

    async def generate_response(
        self,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a response based on the context window and retrieved context.
        
        Args:
            context_window: The conversation history and summary.
            retrieved_context: Grounding context retrieved from search/memory.
            user_prompt: (Optional) The latest user prompt if not already in context_window.messages.
            **kwargs: Extra parameters for the LLM.
            
        Returns:
            The LLM response.
        """
        system_prompt = (
            "You are an AI assistant grounded in the provided context. "
            "You MUST base your response strictly on the retrieved context below. "
            "If the provided context is empty or does not contain enough information to answer the request, "
            "you MUST state explicitly: 'I am uncertain because the evidence is missing.' "
            "You MUST include citations for any facts, data, or code you use from the context.\n\n"
            f"Retrieved Context:\n{retrieved_context}\n"
        )

        if context_window.summary:
            system_prompt += f"\nConversation Summary:\n{context_window.summary}\n"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for msg in context_window.messages:
            messages.append({"role": msg.role, "content": msg.content})

        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        response = await self._llm.chat(messages, **kwargs)
        return response

    async def generate_response_stream(
        self,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        **kwargs: Any
    ) -> Any:
        """
        Generate a streamed response based on the context window and retrieved context.
        """
        system_prompt = (
            "You are an AI assistant grounded in the provided context. "
            "You MUST base your response strictly on the retrieved context below. "
            "If the provided context is empty or does not contain enough information to answer the request, "
            "you MUST state explicitly: 'I am uncertain because the evidence is missing.' "
            "You MUST include citations for any facts, data, or code you use from the context.\n\n"
            f"Retrieved Context:\n{retrieved_context}\n"
        )

        if context_window.summary:
            system_prompt += f"\nConversation Summary:\n{context_window.summary}\n"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for msg in context_window.messages:
            messages.append({"role": msg.role, "content": msg.content})

        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        async for chunk in self._llm.chat_stream(messages, **kwargs):
            yield chunk
