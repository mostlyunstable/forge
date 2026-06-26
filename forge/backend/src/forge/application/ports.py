"""Port interfaces for infrastructure adapters.
These define the contracts that infrastructure must implement.
Application layer depends on these, not on infrastructure."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from uuid import UUID

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.projects.value_objects.project_id import ProjectId


class ICodeIndexer(ABC):
    """Port for code indexing (Tree-sitter adapter)."""

    @abstractmethod
    async def index(self, project_id: ProjectId, repo_path: str) -> list[CodeEntry]:
        """Index a repository and return parsed code entries."""


class IContextRetriever(ABC):
    """Port for context retrieval (vector search adapter)."""

    @abstractmethod
    async def retrieve(self, query: str, project_id: ProjectId) -> dict[str, Any]:
        """Retrieve relevant context for a query."""


class ILLMService(ABC):
    """Port for LLM interactions."""

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if an API key is configured."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        """Send messages to the LLM and return a response."""
