"""Simple TF-IDF + linear classifier for service and category."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score

from ..config import get_settings


class MLClassifier:
    """Wrapper around scikit-learn models for service and category."""

    def __init__(self, models_dir: Path, training_path: Path) -> None:
        self.models_dir = models_dir
        self.training_path = training_path
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.service_model_path = self.models_dir / "svc_type.joblib"
        self.category_model_path = self.models_dir / "category.joblib"
        self._service_model: Pipeline | None = None
        self._category_model: Pipeline | None = None
        self.ensure_models()

    def ensure_models(self) -> None:
        if not self.service_model_path.exists() or not self.category_model_path.exists():
            self.train()
        else:
            self._load_models()

    def _load_models(self) -> None:
        self._service_model = joblib.load(self.service_model_path)
        self._category_model = joblib.load(self.category_model_path)

    def train(self) -> Dict[str, float]:
        texts: list[str] = []
        svc_labels: list[str] = []
        cat_labels: list[str] = []
        with self.training_path.open() as fh:
            for line in fh:
                record = json.loads(line)
                texts.append(record["text"])
                svc_labels.append(record["service_type"])
                cat_labels.append(record["category"])

        svc_model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                (
                    "clf",
                    LogisticRegression(max_iter=100, solver="liblinear", multi_class="auto"),
                ),
            ]
        )
        cat_model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                (
                    "clf",
                    LogisticRegression(max_iter=100, solver="liblinear", multi_class="auto"),
                ),
            ]
        )

        svc_model.fit(texts, svc_labels)
        cat_model.fit(texts, cat_labels)

        joblib.dump(svc_model, self.service_model_path)
        joblib.dump(cat_model, self.category_model_path)

        self._service_model = svc_model
        self._category_model = cat_model

        svc_pred = svc_model.predict(texts)
        cat_pred = cat_model.predict(texts)

        return {
            "service_macro_f1": float(f1_score(svc_labels, svc_pred, average="macro", zero_division=0)),
            "service_micro_f1": float(f1_score(svc_labels, svc_pred, average="micro", zero_division=0)),
            "category_macro_f1": float(f1_score(cat_labels, cat_pred, average="macro", zero_division=0)),
            "category_micro_f1": float(f1_score(cat_labels, cat_pred, average="micro", zero_division=0)),
        }

    def predict(self, text: str) -> Dict[str, Dict[str, float | str]]:
        if self._service_model is None or self._category_model is None:
            self._load_models()

        assert self._service_model is not None
        assert self._category_model is not None

        svc_proba = self._service_model.predict_proba([text])[0]
        svc_labels = list(self._service_model.classes_)
        cat_proba = self._category_model.predict_proba([text])[0]
        cat_labels = list(self._category_model.classes_)

        svc_probs = {label: float(prob) for label, prob in zip(svc_labels, svc_proba)}
        cat_probs = {label: float(prob) for label, prob in zip(cat_labels, cat_proba)}

        top_service = max(svc_probs.items(), key=lambda kv: kv[1])[0]
        top_category = max(cat_probs.items(), key=lambda kv: kv[1])[0]

        return {
            "svc_probs": svc_probs,
            "cat_probs": cat_probs,
            "top": {"service_type": top_service, "category": top_category},
        }


_classifier: MLClassifier | None = None


def get_classifier() -> MLClassifier:
    settings = get_settings()
    global _classifier
    if _classifier is None:
        _classifier = MLClassifier(settings.models_dir, settings.sample_messages_path)
    return _classifier
