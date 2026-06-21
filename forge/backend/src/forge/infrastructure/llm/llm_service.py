"""LLMService - orchestrates LLM interactions."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import structlog
from openai import AsyncOpenAI

from forge.config.settings import get_settings
from forge.config.metrics import LLM_CALLS, LLM_LATENCY

logger = structlog.get_logger()


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: dict[str, int]


class LLMService:
    """Generates responses using an LLM."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: AsyncOpenAI | None = None

    def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs = {"api_key": self._settings.LLM_API_KEY}
            if self._settings.LLM_BASE_URL:
                kwargs["base_url"] = self._settings.LLM_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages to the LLM and return a response."""
        start_time = time.perf_counter()
        try:
            client = self._ensure_client()
            response = await client.chat.completions.create(
                model=self._settings.LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="success").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
            logger.info(
                "llm_call_completed",
                model=self._settings.LLM_MODEL,
                duration=duration,
                tokens=response.usage.total_tokens if response.usage else 0,
            )
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            LLM_CALLS.labels(model=self._settings.LLM_MODEL, status="error").inc()
            LLM_LATENCY.labels(model=self._settings.LLM_MODEL).observe(duration)
            logger.error("llm_call_failed", error=str(e), duration=duration)
            raise
