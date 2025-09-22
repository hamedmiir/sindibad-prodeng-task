from __future__ import annotations

import json

from pathlib import Path

from autotag.app.config import get_settings
from autotag.app.services.ml_classifier import MLClassifier


def test_ml_top1_accuracy(tmp_path: Path) -> None:
    settings = get_settings()
    records = [json.loads(line) for line in settings.sample_messages_path.open()]
    duplicated = records * 2
    split_point = len(duplicated) // 2
    train_records = duplicated[:split_point]
    test_records = duplicated[split_point:]

    training_path = tmp_path / "train.jsonl"
    with training_path.open("w") as fh:
        for record in train_records:
            json.dump(record, fh)
            fh.write("\n")

    classifier = MLClassifier(tmp_path, training_path)
    classifier.train()

    correct_service = 0
    correct_category = 0
    for record in test_records:
        result = classifier.predict(record["text"])
        if result["top"]["service_type"] == record["service_type"]:
            correct_service += 1
        if result["top"]["category"] == record["category"]:
            correct_category += 1

    service_accuracy = correct_service / len(test_records)
    category_accuracy = correct_category / len(test_records)

    assert service_accuracy >= 0.7
    assert category_accuracy >= 0.7
