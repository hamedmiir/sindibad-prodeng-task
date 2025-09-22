"""Mock clarification bot interactions."""
from __future__ import annotations

from typing import Dict, Optional


AMBIGUITIES = {
    "cancellation_modify": {
        "question": "Is the traveler cancelling or modifying the booking?",
        "options": ["cancellation", "modify"],
    }
}


def maybe_question(service_type: Optional[str], category: Optional[str]) -> Optional[Dict[str, object]]:
    """Return a canned question when predictions are ambiguous."""

    if category in {"cancellation", "modify"}:
        return {
            "id": "cancellation_modify",
            **AMBIGUITIES["cancellation_modify"],
        }
    return None


def resolve_answer(ticket_tags: Dict[str, Optional[str]], choice: str) -> Dict[str, Optional[str]]:
    """Update tags based on a user's clarifier answer."""

    updated = dict(ticket_tags)
    if choice in {"cancellation", "modify"}:
        updated["category"] = choice
    return updated
