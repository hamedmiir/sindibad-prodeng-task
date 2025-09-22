"""Keyword-based tagging rules."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..config import get_settings


@dataclass
class Rule:
    id: str
    pattern: str
    lang: str
    precision: str

    def matches(self, text: str, lang: str) -> bool:
        if self.lang not in {"*", lang}:
            return False
        return re.search(self.pattern, text, flags=re.IGNORECASE) is not None


class RulesEngine:
    """Simple keyword matcher loaded from YAML."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.service_rules: List[Rule] = []
        self.category_rules: List[Rule] = []
        self._load()

    def _load(self) -> None:
        data = yaml.safe_load(self.path.read_text())
        self.service_rules = [Rule(**item) for item in data.get("service_type", [])]
        self.category_rules = [Rule(**item) for item in data.get("category", [])]

    def apply_rules(self, text: str, lang: str) -> Dict[str, Optional[object]]:
        service_hits: List[str] = []
        category_hits: List[str] = []
        service_type: Optional[str] = None
        category: Optional[str] = None
        precision_hint = "normal"

        for rule in self.service_rules:
            if rule.matches(text, lang):
                service_hits.append(rule.id)
                precision_hint = "high" if rule.precision == "high" else precision_hint
                if service_type is None:
                    if "wallet" in rule.id:
                        service_type = "wallet"
                    elif "flight" in rule.id:
                        service_type = "flight"
                    elif "hotel" in rule.id:
                        service_type = "hotel"
                    elif "visa" in rule.id:
                        service_type = "visa"
                    elif "esim" in rule.id:
                        service_type = "esim"

        for rule in self.category_rules:
            if rule.matches(text, lang):
                category_hits.append(rule.id)
                precision_hint = "high" if rule.precision == "high" else precision_hint
                if category is None:
                    if "cancel" in rule.id:
                        category = "cancellation"
                    elif "topup" in rule.id or "top_up" in rule.id:
                        category = "top_up"
                    elif "withdraw" in rule.id:
                        category = "withdraw"

        result: Dict[str, Optional[object]] = {
            "service_type": service_type,
            "category": category,
            "hits": service_hits + category_hits,
            "precision_hint": precision_hint,
        }
        return result


_rules_engine: Optional[RulesEngine] = None


def get_rules_engine() -> RulesEngine:
    """Return a singleton rules engine."""

    global _rules_engine
    if _rules_engine is None:
        settings = get_settings()
        _rules_engine = RulesEngine(settings.rules_path)
    return _rules_engine
