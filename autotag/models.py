"""Backwards-compatible shim for ORM models."""

from __future__ import annotations

from .app.models import Message, TagAudit, Ticket

__all__ = ["Message", "TagAudit", "Ticket"]
