"""Utilities for persisting tag decisions."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models import TagAudit, Ticket


def write_tags(
    db: Session,
    ticket: Ticket,
    service_type: Optional[str],
    category: Optional[str],
    confidence: float,
    source: str,
    reason: Optional[str] = None,
) -> Ticket:
    """Persist chosen tags and audit the change."""

    if (
        ticket.service_type == service_type
        and ticket.category == category
        and ticket.tag_source == source
        and (ticket.tag_confidence or 0.0) == confidence
    ):
        return ticket

    audit = TagAudit(
        ticket_id=ticket.ticket_id,
        old_service_type=ticket.service_type,
        old_category=ticket.category,
        new_service_type=service_type,
        new_category=category,
        confidence=confidence,
        source=source,
        reason=reason,
    )
    db.add(audit)

    ticket.service_type = service_type
    ticket.category = category
    ticket.tag_confidence = confidence
    ticket.tag_source = source
    db.add(ticket)

    return ticket
