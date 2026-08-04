"""LLMService - orchestrates LLM interactions."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import openai
import structlog
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from forge.config.metrics import LLM_CALLS, LLM_LATENCY
from forge.config.settings import get_settings

logger = structlog.get_logger()


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    tool_calls: list[dict[str, Any]] | None = None


class LLMService:
    """Generates responses using an LLM."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: AsyncOpenAI | None = None

    @property
    def is_configured(self) -> bool:
        """Check if an API key is configured for LLM calls."""
        return bool(self._settings.LLM_API_KEY)

    def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs: dict = {
                "api_key": self._settings.LLM_API_KEY,
                "timeout": 60.0,  # 60s for cold-start models like NVIDIA NIM
            }
            if self._settings.LLM_BASE_URL:
                kwargs["base_url"] = self._settings.LLM_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    @retry(
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages to the LLM and return a response."""
        start_time = time.perf_counter()
        try:
            client = self._ensure_client()
            kwargs: dict[str, Any] = {
                "model": self._settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            response = await client.chat.completions.create(**kwargs)
            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="success").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
            logger.info(
                "llm_call_completed",
                model=self._settings.LLM_MODEL,
                duration=duration,
                tokens=response.usage.total_tokens if response.usage else 0,
            )

            message = response.choices[0].message
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ]

            return LLMResponse(
                content=message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                tool_calls=tool_calls,
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="error").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
            logger.error("llm_call_failed", error=str(e), duration=duration)
            raise

    @retry(
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        """Send messages to the LLM and yield response chunks."""
        start_time = time.perf_counter()
        try:
            client = self._ensure_client()
            kwargs: dict[str, Any] = {
                "model": self._settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools

            stream = await client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="success").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
        except Exception as e:
            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="error").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
            logger.error("llm_stream_failed", error=str(e), duration=duration)
            raise
