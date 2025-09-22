"""Message ingestion endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..deps import get_db
from ..models import Message, Ticket
from ..services import clarification_bot, confidence_policy, lang_and_scrub, llm_adjudicator
from ..services.ml_classifier import get_classifier
from ..services.rules_engine import get_rules_engine
from ..services.tag_writer import write_tags

router = APIRouter(prefix="/messages", tags=["messages"])


def _next_ticket_id(db: Session) -> str:
    count = db.query(Ticket).count()
    return f"TK{count + 1:04d}"


def _get_or_create_ticket(db: Session, conversation_id: str) -> Ticket:
    ticket = db.query(Ticket).filter_by(conversation_id=conversation_id).first()
    if ticket:
        return ticket
    ticket = Ticket(ticket_id=_next_ticket_id(db), conversation_id=conversation_id)
    db.add(ticket)
    db.flush()
    return ticket


def _conversation_text(ticket: Ticket) -> str:
    """Concatenate scrubbed message text for downstream tagging."""

    combined = " ".join(msg.text for msg in ticket.messages if msg.text)
    return combined.strip()


@router.post("/ingest", response_model=schemas.IngestOut)
def ingest_message(payload: schemas.MessageIn, db: Session = Depends(get_db)) -> schemas.IngestOut:
    settings = get_settings()
    ticket = _get_or_create_ticket(db, payload.conversation_id)
    lang = lang_and_scrub.detect_lang(payload.text)
    clean_text, redactions = lang_and_scrub.scrub_pii(payload.text)

    message = Message(
        sender=payload.sender,
        text=clean_text,
        lang=lang,
        pii_redactions=redactions,
    )
    ticket.messages.append(message)
<<<<<<< Updated upstream
=======
    # Flush first so message.ts is populated by default factory
    db.flush()
    ticket.updated_at = message.ts
>>>>>>> Stashed changes
    db.flush()
    ticket.updated_at = message.ts or datetime.utcnow()

    conversation_text = _conversation_text(ticket) or clean_text
    rules = get_rules_engine().apply_rules(conversation_text, lang)
    ml_result = get_classifier().predict(conversation_text)
    decision = confidence_policy.evaluate(rules, ml_result)

    final_service = decision["service_type"]
    final_category = decision["category"]
    final_confidence = float(decision["confidence"])
    source = str(decision["source"])
    clarifier: Optional[dict] = None

    if decision["action"] == "auto":
        write_tags(db, ticket, final_service, final_category, final_confidence, source)
    elif decision["action"] == "llm":
        llm_result = llm_adjudicator.adjudicate(
            conversation_text,
            {"service_type": final_service, "category": final_category},
        )
        final_service = llm_result.get("service_type") or final_service
        final_category = llm_result.get("category") or final_category
        final_confidence = float(llm_result.get("confidence", final_confidence))
        source = "llm"
        if final_confidence >= settings.high_threshold:
            write_tags(db, ticket, final_service, final_category, final_confidence, source)
        else:
            clarifier = clarification_bot.maybe_question(final_service, final_category)
    else:
        clarifier = clarification_bot.maybe_question(final_service, final_category)

    db.commit()

    return schemas.IngestOut(
        ticket_id=ticket.ticket_id,
        suggested_tags=schemas.SuggestedTags(
            service_type=final_service,
            category=final_category,
        ),
        confidence=final_confidence,
        source=source,
        clarifier_question=clarifier,
    )
