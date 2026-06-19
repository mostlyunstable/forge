"""Domain events infrastructure.

Events represent something meaningful that happened in the domain.
They are published by use cases and consumed by event handlers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events.

    Events are immutable value objects that capture something that happened.
    They carry data about the occurrence but commands (intent to do something).
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Short string identifying the event type (e.g., 'project.created')."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize event for storage or transmission."""
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": self.metadata,
        }


class IEventBus(Protocol):
    """Interface for publishing domain events."""

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event."""
        ...

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events in order."""
        ...


class IEventHandler(Protocol):
    """Interface for handling domain events."""

    @property
    def event_type(self) -> str:
        """The event type this handler listens for."""
        ...

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        ...
