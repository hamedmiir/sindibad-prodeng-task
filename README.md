# AutoTag Service Skeleton

A minimal hybrid (rules → ML → LLM stub → clarifier) ticket auto-tagger built with FastAPI, SQLite, and scikit-learn.

## Quick start

### Local

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make seed
make dev
```

In another terminal run the example cURL requests below.

### Docker

```bash
make docker
# then run the container, exposing port 8000
```

## Make targets

- `make install` – install the project in editable mode with dev extras.
- `make dev` – start the FastAPI app with Uvicorn reloader.
- `make seed` – populate the SQLite database with sample tickets/messages.
- `make retrain` – retrain the scikit-learn models on `app/data/sample_messages.jsonl`.
- `make test` – run the pytest suite.

## Example requests

```bash
curl -X POST localhost:8000/messages/ingest -H "content-type: application/json" \
 -d '{"conversation_id":"c1","text":"please top up my wallet","sender":"user"}'

curl -X POST localhost:8000/tickets/TK1/override -H "content-type: application/json" \
 -d '{"service_type":"wallet","category":"withdraw","reason":"agent correction"}'

curl -X GET localhost:8000/tickets
```

## Confidence thresholds & rules tuning

Confidence bands are defined in `app/config.py` (`τ_high=0.80`, `τ_low=0.55`).
High-precision rules (marked `precision: high` in `app/data/rules.yaml`) force confidence to ≥0.9.
Adjust or add regex patterns in `rules.yaml` to capture new keywords or markets.

Models live in `app/data/models/`. If absent, they are trained on startup using the sample dataset.

Explore metrics via `GET /admin/metrics`, and retrain models with `POST /admin/retrain`. Ticket listings aggregate conversation history so the tagging engine always evaluates the full thread when classifying.
