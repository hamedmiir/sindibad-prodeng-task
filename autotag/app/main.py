"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .db import create_all
from .services.ml_classifier import get_classifier
from .routers import messages, tickets, tagging


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def _startup() -> None:
        create_all()
        get_classifier().ensure_models()

    app.include_router(messages.router)
    app.include_router(tickets.router)
    app.include_router(tagging.router)

    return app


app = create_app()
