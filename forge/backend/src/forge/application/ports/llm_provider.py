from abc import ABC, abstractmethod
from typing import Any

class ILLMProvider(ABC):
    """Port for LLM model inference used by the Reasoning Engine."""
    
    @abstractmethod
    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> Any:
        """
        Send messages to the LLM and return a response.
        
        Args:
            messages: A list of message dictionaries.
            tools: Optional list of tool schemas.
            **kwargs: Additional parameters.
        """
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> Any:
        """
        Send messages to the LLM and return a stream of response chunks.
        """
        pass
