"""Tagging utilities including admin endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import TagAudit, Ticket
from ..services import clarification_bot
from ..services.ml_classifier import get_classifier
from ..services.tag_writer import write_tags
from .tickets import _ticket_or_404, _to_schema

router = APIRouter(tags=["tagging"])


def compute_metrics(db: Session) -> dict:
    total_tickets = db.query(func.count(Ticket.ticket_id)).scalar() or 0
    auto_tickets = (
        db.query(func.count(Ticket.ticket_id))
        .filter(Ticket.tag_source.in_(["rule", "ml", "llm"]))
        .scalar()
        or 0
    )
    override_events = (
        db.query(func.count(TagAudit.audit_id))
        .filter(TagAudit.source == "agent")
        .scalar()
        or 0
    )
    llm_hits = (
        db.query(func.count(Ticket.ticket_id))
        .filter(Ticket.tag_source == "llm")
        .scalar()
        or 0
    )
    class_distribution: dict[str, int] = {}
    for service_type, category, count in (
        db.query(Ticket.service_type, Ticket.category, func.count(Ticket.ticket_id))
        .group_by(Ticket.service_type, Ticket.category)
        .all()
    ):
        key = f"{service_type or 'unknown'}::{category or 'unknown'}"
        class_distribution[key] = count

    auto_rate = auto_tickets / total_tickets if total_tickets else 0.0
    override_rate = override_events / total_tickets if total_tickets else 0.0
    llm_rate = llm_hits / total_tickets if total_tickets else 0.0

    return {
        "auto_tag_rate": auto_rate,
        "override_rate": override_rate,
        "class_distribution": class_distribution,
        "llm_hit_rate": llm_rate,
        "tickets": total_tickets,
    }


@router.post("/admin/retrain")
def retrain_models(db: Session = Depends(get_db)) -> dict:
    metrics = get_classifier().train()
    db.commit()
    return metrics


@router.get("/admin/metrics")
def admin_metrics(db: Session = Depends(get_db)) -> dict:
    return compute_metrics(db)


@router.post("/clarifier/reply", response_model=schemas.TicketOut)
def clarifier_reply(
    payload: schemas.ClarifierReplyIn, db: Session = Depends(get_db)
) -> schemas.TicketOut:
    ticket = _ticket_or_404(db, payload.ticket_id)
    if not ticket.messages:
        raise HTTPException(status_code=400, detail="No messages for ticket")
    updated = clarification_bot.resolve_answer(
        {"service_type": ticket.service_type, "category": ticket.category},
        payload.choice,
    )
    write_tags(
        db,
        ticket,
        updated.get("service_type"),
        updated.get("category"),
        confidence=max(ticket.tag_confidence or 0.6, 0.6),
        source="user",
    )
    db.commit()
    db.refresh(ticket)
    return _to_schema(ticket)
