"""Decision policy for tagging confidence."""
from __future__ import annotations

from typing import Dict, Optional

from ..config import get_settings

ALLOWED_PAIRS = {
    ("flight", "cancellation"),
    ("flight", "modify"),
    ("flight", "order_recheck"),
    ("hotel", "modify"),
    ("hotel", "cancellation"),
    ("visa", "pre_purchase"),
    ("wallet", "top_up"),
    ("wallet", "withdraw"),
    ("wallet", "cancellation"),
    ("esim", "pre_purchase"),
}


def _is_valid_pair(service_type: Optional[str], category: Optional[str]) -> bool:
    if service_type is None or category is None:
        return True
    if category == "others" or service_type == "other":
        return True
    return (service_type, category) in ALLOWED_PAIRS


def evaluate(rule_result: Dict[str, object], ml_result: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    """Combine rule and ML signals into a confidence decision."""

    settings = get_settings()
    service_type = rule_result.get("service_type") or ml_result["top"]["service_type"]
    category = rule_result.get("category") or ml_result["top"]["category"]
    svc_probs: Dict[str, float] = {
        k: float(v) for k, v in ml_result["svc_probs"].items()  # type: ignore[arg-type]
    }
    cat_probs: Dict[str, float] = {
        k: float(v) for k, v in ml_result["cat_probs"].items()  # type: ignore[arg-type]
    }
    svc_score = svc_probs.get(service_type, 0.4)
    cat_score = cat_probs.get(category, 0.4)
    confidence = min(svc_score, cat_score)

    source = "ml"
    if rule_result.get("hits"):
        source = "rule"
        confidence = max(confidence, 0.75)
        if rule_result.get("precision_hint") == "high":
            confidence = max(confidence, 0.9)

    if not _is_valid_pair(service_type, category):
        confidence = min(confidence, 0.4)

    if confidence >= settings.high_threshold:
        action = "auto"
    elif confidence >= settings.low_threshold:
        action = "llm"
    else:
        action = "clarify"

    return {
        "service_type": service_type,
        "category": category,
        "confidence": float(confidence),
        "action": action,
        "source": source,
    }
