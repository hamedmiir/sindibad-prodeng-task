"""Deterministic stub to mimic an LLM adjudicator."""
from __future__ import annotations

from typing import Dict


HEURISTICS = {
    "cancel": ("cancellation", 0.8),
    "refund": ("cancellation", 0.75),
    "top up": ("top_up", 0.78),
    "withdraw": ("withdraw", 0.8),
    "change": ("modify", 0.7),
    "modify": ("modify", 0.7),
}


def adjudicate(text: str, current: Dict[str, str]) -> Dict[str, object]:
    """Return revised tags with a canned rationale."""

    lower = text.lower()
    category = current.get("category")
    service_type = current.get("service_type")
    confidence = 0.65
    rationale = "Using heuristic fallback"

    for key, (cat, conf) in HEURISTICS.items():
        if key in lower:
            category = cat
            confidence = max(confidence, conf)
            rationale = f"Detected keyword '{key}'"
            break

    if "wallet" in lower:
        service_type = "wallet"
        confidence = max(confidence, 0.78)
        rationale += " + wallet keyword"
    elif "flight" in lower or "pnr" in lower:
        service_type = "flight"
        confidence = max(confidence, 0.76)
        rationale += " + flight keyword"

    return {
        "service_type": service_type,
        "category": category,
        "confidence": float(confidence),
        "rationale": rationale,
    }
