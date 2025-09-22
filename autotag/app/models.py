"""Database models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Ticket(Base):
    """Ticket for a support conversation."""

    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    service_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tag_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    tag_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="Message.message_id"
    )
    audits: Mapped[list["TagAudit"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TagAudit.audit_id"
    )


class Message(Base):
    """Individual message within a ticket."""

    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"))
    sender: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(String)
    lang: Mapped[str] = mapped_column(String, default="en")
    pii_redactions: Mapped[list[str]] = mapped_column(JSON, default=list)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped[Ticket] = relationship(back_populates="messages")


class TagAudit(Base):
    """Audit trail for tag changes."""

    __tablename__ = "tag_audits"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"))
    old_service_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    old_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_service_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(String)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped[Ticket] = relationship(back_populates="audits")
