"""In-memory event bus for development and testing."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Callable, Awaitable

import structlog

from forge.domain.shared.events import DomainEvent, IEventHandler

logger = structlog.get_logger()


class InMemoryEventBus:
    """Simple in-memory event bus that dispatches events to registered handlers.

    For production, replace with a message broker (RabbitMQ, Kafka, Redis Streams).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[IEventHandler]] = defaultdict(list)
        self._published: list[DomainEvent] = []

    def register(self, handler: IEventHandler) -> None:
        """Register an event handler."""
        self._handlers[handler.event_type].append(handler)
        logger.debug("event_handler_registered", event_type=handler.event_type, handler=type(handler).__name__)

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event to all registered handlers."""
        self._published.append(event)
        # Get handlers for specific event type + wildcard handlers
        specific_handlers = self._handlers.get(event.event_type, [])
        wildcard_handlers = self._handlers.get("*", [])
        handlers = specific_handlers + wildcard_handlers

        logger.info(
            "event_published",
            event_type=event.event_type,
            event_id=str(event.event_id),
            handler_count=len(handlers),
        )

        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event.event_type,
                    handler=type(handler).__name__,
                    error=str(e),
                )

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events in order."""
        for event in events:
            await self.publish(event)

    def get_published(self) -> list[DomainEvent]:
        """Return all published events (for testing)."""
        return list(self._published)

    def clear(self) -> None:
        """Clear all published events (for testing)."""
        self._published.clear()


event_bus = InMemoryEventBus()
