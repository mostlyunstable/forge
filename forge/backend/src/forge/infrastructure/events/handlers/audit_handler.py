"""Audit logging event handler.

Logs all domain events for audit trail and debugging.
"""

from __future__ import annotations

import structlog

from forge.domain.shared.events import DomainEvent

logger = structlog.get_logger("audit")


class AuditLogHandler:
    """Logs all domain events for audit trail."""

    # Wildcard handler - listens for ALL event types
    event_type = "*"

    async def handle(self, event: DomainEvent) -> None:
        """Log the event."""
        logger.info(
            "domain_event",
            event_type=event.event_type,
            event_id=str(event.event_id),
            occurred_at=event.occurred_at.isoformat(),
            data=event.to_dict(),
        )
