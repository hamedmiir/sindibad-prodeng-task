"""FastAPI dependencies."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from .db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request scope."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
