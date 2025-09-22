"""Language detection and PII scrubbing utilities."""
from __future__ import annotations

import re
from typing import List, Tuple

EMAIL_RE = re.compile(r"[\w.\-]+@[\w.\-]+")
PHONE_RE = re.compile(r"\b\+?\d[\d\-\s]{7,}\b")


def detect_lang(text: str) -> str:
    """A trivial language detector returning English for now."""

    return "en"


def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """Redact basic email and phone patterns."""

    redactions: List[str] = []
    clean_text = text

    for pattern in (EMAIL_RE, PHONE_RE):
        for match in pattern.findall(text):
            redactions.append(match)
            clean_text = clean_text.replace(match, "<redacted>")

    return clean_text, redactions
