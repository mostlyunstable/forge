from abc import ABC, abstractmethod
from typing import Any

class ILLMProvider(ABC):
    """Port for LLM model inference used by the Reasoning Engine."""
    
    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """
        Send messages to the LLM and return a response string.
        
        Args:
            messages: A list of message dictionaries with 'role' and 'content'.
            **kwargs: Additional parameters like temperature, max_tokens, etc.
            
        Returns:
        """
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        """
        Send messages to the LLM and return a stream of response chunks.
        
        Args:
            messages: A list of message dictionaries with 'role' and 'content'.
            **kwargs: Additional parameters like temperature, max_tokens, etc.
            
        Returns:
            An async generator yielding response strings.
        """
        pass
