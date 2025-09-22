"""Populate the SQLite database with sample tickets and messages."""
from __future__ import annotations

import json

from ..config import get_settings
from ..db import create_all, session_scope
from ..models import Message, Ticket
from ..services import confidence_policy, lang_and_scrub
from ..services.ml_classifier import get_classifier
from ..services.rules_engine import get_rules_engine
from ..services.tag_writer import write_tags


def main() -> None:
    settings = get_settings()
    create_all()
    classifier = get_classifier()
    rules = get_rules_engine()

    with session_scope() as db:
        existing = {ticket.conversation_id for ticket in db.query(Ticket).all()}
        with settings.sample_messages_path.open() as fh:
            for idx, line in enumerate(fh, start=1):
                record = json.loads(line)
                conversation_id = f"seed_{idx}"
                if conversation_id in existing:
                    continue
                ticket = Ticket(ticket_id=f"TKSEED{idx:03d}", conversation_id=conversation_id)
                db.add(ticket)
                db.flush()

                lang = lang_and_scrub.detect_lang(record["text"])
                clean_text, redactions = lang_and_scrub.scrub_pii(record["text"])
                message = Message(
                    sender="user",
                    text=clean_text,
                    lang=lang,
                    pii_redactions=redactions,
                )
                ticket.messages.append(message)
                ticket.updated_at = message.ts
                db.flush()

                conversation_text = " ".join(
                    msg.text for msg in ticket.messages if msg.text
                ).strip()
                rule_hit = rules.apply_rules(conversation_text, lang)
                ml_result = classifier.predict(conversation_text)
                decision = confidence_policy.evaluate(rule_hit, ml_result)
                write_tags(
                    db,
                    ticket,
                    decision["service_type"],
                    decision["category"],
                    float(decision["confidence"]),
                    decision["source"],
                )


if __name__ == "__main__":
    main()
