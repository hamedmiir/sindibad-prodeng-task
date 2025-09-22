"""CLI entrypoint to retrain the ML models."""
from __future__ import annotations

from pprint import pprint

from ..config import get_settings
from ..services.ml_classifier import get_classifier


def main() -> None:
    settings = get_settings()
    classifier = get_classifier()
    metrics = classifier.train()
    pprint(metrics)
    print(f"Models saved to {settings.models_dir}")


if __name__ == "__main__":
    main()
