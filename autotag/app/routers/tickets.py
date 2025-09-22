"""Ticket retrieval and override endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import Ticket
from ..services.tag_writer import write_tags

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _ticket_or_404(db: Session, ticket_id: str) -> Ticket:
    ticket = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def _to_summary(ticket: Ticket) -> schemas.TicketSummary:
    last_message = ticket.messages[-1].text if ticket.messages else None
    preview = last_message[:120] if last_message else None
    return schemas.TicketSummary(
        ticket_id=ticket.ticket_id,
        conversation_id=ticket.conversation_id,
        service_type=ticket.service_type,
        category=ticket.category,
        status=ticket.status,
        updated_at=ticket.updated_at,
        message_count=len(ticket.messages),
        last_message_preview=preview,
    )


def _to_schema(ticket: Ticket) -> schemas.TicketOut:
    return schemas.TicketOut(
        ticket_id=ticket.ticket_id,
        conversation_id=ticket.conversation_id,
        service_type=ticket.service_type,
        category=ticket.category,
        tag_confidence=ticket.tag_confidence,
        tag_source=ticket.tag_source,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages=[
            schemas.MessageOut(
                message_id=msg.message_id,
                sender=msg.sender,
                text=msg.text,
                lang=msg.lang,
                pii_redactions=msg.pii_redactions or [],
                ts=msg.ts,
            )
            for msg in ticket.messages
        ],
        tag_history=[
            schemas.TagAuditOut(
                audit_id=audit.audit_id,
                old_service_type=audit.old_service_type,
                old_category=audit.old_category,
                new_service_type=audit.new_service_type,
                new_category=audit.new_category,
                confidence=audit.confidence,
                source=audit.source,
                reason=audit.reason,
                ts=audit.ts,
            )
            for audit in ticket.audits
        ],
    )


@router.get("", response_model=list[schemas.TicketSummary])
def list_tickets(db: Session = Depends(get_db)) -> list[schemas.TicketSummary]:
    """Return all tickets ordered by recency."""

    tickets = db.query(Ticket).order_by(Ticket.updated_at.desc(), Ticket.ticket_id).all()
    return [_to_summary(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)) -> schemas.TicketOut:
    ticket = _ticket_or_404(db, ticket_id)
    return _to_schema(ticket)


@router.post("/{ticket_id}/override", response_model=schemas.TicketOut)
def override_ticket(
    ticket_id: str, payload: schemas.OverrideIn, db: Session = Depends(get_db)
) -> schemas.TicketOut:
    ticket = _ticket_or_404(db, ticket_id)
    write_tags(
        db,
        ticket,
        payload.service_type,
        payload.category,
        confidence=1.0,
        source="agent",
        reason=payload.reason,
    )
    db.commit()
    db.refresh(ticket)
    return _to_schema(ticket)
