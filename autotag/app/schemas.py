"""Pydantic schemas for API requests and responses."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

ServiceType = Literal["flight", "hotel", "visa", "esim", "wallet", "other"]
Category = Literal[
    "cancellation",
    "modify",
    "top_up",
    "withdraw",
    "order_recheck",
    "pre_purchase",
    "others",
]


class MessageIn(BaseModel):
    conversation_id: str
    text: Annotated[str, Field(min_length=1)]
    sender: Literal["user", "agent", "bot"]


class SuggestedTags(BaseModel):
    service_type: Optional[str]
    category: Optional[str]


class IngestOut(BaseModel):
    ticket_id: str
    suggested_tags: SuggestedTags
    confidence: float
    source: str
    clarifier_question: Optional[dict]


class MessageOut(BaseModel):
    message_id: int
    sender: str
    text: str
    lang: str
    pii_redactions: list[str]
    ts: datetime


class TagAuditOut(BaseModel):
    audit_id: int
    old_service_type: Optional[str]
    old_category: Optional[str]
    new_service_type: Optional[str]
    new_category: Optional[str]
    confidence: Optional[float]
    source: str
    reason: Optional[str]
    ts: datetime


class TicketOut(BaseModel):
    ticket_id: str
    conversation_id: str
    service_type: Optional[str]
    category: Optional[str]
    tag_confidence: Optional[float]
    tag_source: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]
    tag_history: list[TagAuditOut]


class TicketSummary(BaseModel):
    """Compact representation used for list views."""

    ticket_id: str
    conversation_id: str
    service_type: Optional[str]
    category: Optional[str]
    status: str
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str]


class OverrideIn(BaseModel):
    service_type: str
    category: str
    reason: Annotated[str, Field(min_length=1)]


class ClarifierReplyIn(BaseModel):
    ticket_id: str
    choice: str
