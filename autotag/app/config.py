"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the auto-tagging service."""

    app_name: str = "AutoTag Service"
    database_url: str = (
        "sqlite:///" + str(Path(__file__).resolve().parent.parent / "autotag.db")
    )
    models_dir: Path = Path(__file__).resolve().parent / "data" / "models"
    sample_messages_path: Path = Path(__file__).resolve().parent / "data" / "sample_messages.jsonl"
    rules_path: Path = Path(__file__).resolve().parent / "data" / "rules.yaml"
    high_threshold: float = 0.80
    low_threshold: float = 0.55

    class Config:
        env_prefix = "AUTOTAG_"
        env_file = ".env"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
