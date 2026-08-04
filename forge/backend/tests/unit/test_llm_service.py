import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from forge.infrastructure.llm.llm_service import LLMService

@pytest.fixture
def service():
    with patch("forge.infrastructure.llm.llm_service.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "test-model"
        mock_settings.LLM_BASE_URL = None
        mock_get_settings.return_value = mock_settings
        return LLMService()

@pytest.mark.asyncio
async def test_chat_success(service):
    with patch("forge.infrastructure.llm.llm_service.AsyncOpenAI") as MockClient:
        mock_client = MagicMock()
        mock_chat_completion = MagicMock()
        
        mock_message = MagicMock()
        mock_message.content = "response content"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_chat_completion.choices = [mock_choice]
        mock_chat_completion.usage = mock_usage
        mock_chat_completion.model = "test-model"
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_chat_completion)
        MockClient.return_value = mock_client
        
        response = await service.chat([{"role": "user", "content": "hi"}])
        
        assert response.content == "response content"
        assert response.usage["total_tokens"] == 30
        assert response.tool_calls is None

@pytest.mark.asyncio
async def test_chat_with_tools(service):
    with patch("forge.infrastructure.llm.llm_service.AsyncOpenAI") as MockClient:
        mock_client = MagicMock()
        mock_chat_completion = MagicMock()
        
        mock_tc = MagicMock()
        mock_tc.id = "call_1"
        mock_tc.type = "function"
        mock_tc.function.name = "my_func"
        mock_tc.function.arguments = "{}"
        
        mock_message = MagicMock()
        mock_message.content = None
        mock_message.tool_calls = [mock_tc]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_chat_completion.choices = [mock_choice]
        mock_chat_completion.usage = None
        mock_chat_completion.model = "test-model"
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_chat_completion)
        MockClient.return_value = mock_client
        
        response = await service.chat(
            [{"role": "user", "content": "hi"}],
            tools=[{"type": "function", "function": {"name": "my_func"}}]
        )
        
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["id"] == "call_1"
        assert response.tool_calls[0]["function"]["name"] == "my_func"
        
@pytest.mark.asyncio
async def test_chat_failure(service):
    with patch("forge.infrastructure.llm.llm_service.AsyncOpenAI") as MockClient:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        MockClient.return_value = mock_client
        
        # tenacity retry will re-raise the exception if we mock retry completely or if it's not a retryable exception
        with pytest.raises(Exception):
            await service.chat([{"role": "user", "content": "hi"}])

@pytest.mark.asyncio
async def test_chat_stream(service):
    with patch("forge.infrastructure.llm.llm_service.AsyncOpenAI") as MockClient:
        mock_client = MagicMock()
        
        async def mock_stream():
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = "chunk"
            yield mock_chunk
            
            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [MagicMock()]
            mock_chunk2.choices[0].delta.content = "2"
            yield mock_chunk2
            
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        MockClient.return_value = mock_client
        
        chunks = []
        async for chunk in service.chat_stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)
            
        assert chunks == ["chunk", "2"]

@pytest.mark.asyncio
async def test_chat_stream_failure(service):
    with patch("forge.infrastructure.llm.llm_service.AsyncOpenAI") as MockClient:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        MockClient.return_value = mock_client
        
        with pytest.raises(Exception):
            async for chunk in service.chat_stream([{"role": "user", "content": "hi"}]):
                pass

def test_is_configured(service):
    assert service.is_configured is True
