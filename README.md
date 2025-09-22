# AutoTag Service Skeleton

A minimal hybrid (rules → ML → LLM stub → clarifier) ticket auto-tagger built with FastAPI, SQLite, and scikit-learn. Follow the steps below to install dependencies, seed the database with example conversations, run the API locally or in Docker, execute the test suite, and try the sample endpoints.

## Project overview

AutoTag Service ingests support conversations and automatically assigns a `service_type`/`category` to the underlying ticket. It layers several techniques to maximize accuracy while remaining explainable:

1. **Rules engine** – deterministic keyword/regex patterns loaded from [`app/data/rules.yaml`](autotag/app/data/rules.yaml) provide high-precision matches and confidence hints.
2. **ML classifier** – scikit-learn TF–IDF + Logistic Regression models produce probability distributions for both service and category.
3. **LLM adjudicator (stub)** – a deterministic heuristic mimicking a cheap LLM adjusts tags when confidence is marginal.
4. **Clarifier bot** – asks the user a targeted question when the system is still uncertain; the response finalizes the ticket tags.

The pipeline persists messages, tickets, and audit history in SQLite via SQLAlchemy models. Confidence thresholds (`τ_high=0.80`, `τ_low=0.55`) are configured in [`app/config.py`](autotag/app/config.py).

### Data model

| Table      | Fields (subset)                                                                 | Notes                                               |
|------------|---------------------------------------------------------------------------------|-----------------------------------------------------|
| `Ticket`   | `ticket_id`, `conversation_id`, `service_type`, `category`, `tag_confidence`,<br>`tag_source`, `status`, timestamps | Holds the current classification for a conversation. |
| `Message`  | `message_id`, `ticket_id`, `sender`, `text`, `lang`, `pii_redactions`, `ts`      | Stores scrubbed conversation messages.              |
| `TagAudit` | `audit_id`, `ticket_id`, `old_service_type`, `new_service_type`, `confidence`,<br>`source`, `reason`, `ts` | Tracks every change to the ticket tags.             |

### Tagging pipeline

1. **Ingest** – `/messages/ingest` accepts a new message, detects language, and redacts PII.
2. **Persist** – the message is appended to the ticket (created if needed).
3. **Evaluate** – combines conversation text, applies the rules engine and ML classifier, and feeds results into the confidence policy.
4. **Decide** – the policy chooses to auto-apply tags, escalate to the LLM adjudicator, or request clarification.
5. **Clarify** – if needed, `/clarifier/reply` records a user response and finalizes tags.

### Core service components

- `rules_engine`: loads YAML rules, returns tentative tags, rule hits, and precision hints.
- `ml_classifier`: manages two classifiers (service & category); trains from [`app/data/sample_messages.jsonl`](autotag/app/data/sample_messages.jsonl) if models are missing.
- `confidence_policy`: fuses rule and ML scores, enforces valid tag combinations, and decides between automatic tagging, LLM review, or clarification.
- `llm_adjudicator`: deterministic heuristic that simulates an LLM to revise tags and boost confidence.
- `clarification_bot`: generates disambiguation questions and applies user answers.
- `tag_writer`: writes tags to the `Ticket` table and appends `TagAudit` entries.

### REST API surface

| Method & Path | Request model       | Response model  | Purpose |
|---------------|---------------------|-----------------|---------|
| `POST /messages/ingest` | `MessageIn`          | `IngestOut`      | Add a message, run tagging pipeline, optionally emit clarifier question. |
| `GET /tickets` | –                   | `[TicketSummary]` | List tickets sorted by `updated_at`. |
| `GET /tickets/{ticket_id}` | –        | `TicketOut`      | Fetch a ticket with messages and tag audit history. |
| `POST /tickets/{ticket_id}/override` | `OverrideIn` | `TicketOut`      | Manually set tags with confidence 1.0 and source `agent`. |
| `POST /admin/retrain` | –             | metrics dict     | Retrain scikit-learn models and return macro/micro F1 metrics. |
| `GET /admin/metrics` | –              | metrics dict     | Aggregated tagging statistics and ticket counts. |
| `POST /clarifier/reply` | `ClarifierReplyIn` | `TicketOut` | Apply a user’s answer to finalize tags after clarification. |

These Pydantic schemas live in [`autotag/app/schemas`](autotag/app/schemas/).

### End-to-end flow at a glance

```mermaid
flowchart TD
    A[User message] --> B[/messages/ingest]
    B --> C[Store Message & Ticket]
    C --> D[rules_engine]
    C --> E[ml_classifier]
    D --> F[confidence_policy]
    E --> F
    F -->|auto| G[tag_writer]
    F -->|llm| H[llm_adjudicator]
    H --> F
    F -->|clarify| I[clarification_bot]
    I --> J[/clarifier/reply]
    J --> G
```

The flow ensures every message is persisted before classification, producing an audit trail and deterministic replayability for debugging.

## Requirements

- Python 3.11 or later and `pip`.
- SQLite (ships with Python, no external service required).
- `make` for the provided convenience targets (optional but recommended).
- `curl` for hitting the example endpoints.
- Docker 24+ (optional) if you want to run the service in a container.

## Local setup and development server

```bash
git clone <repository-url>
cd sindibad-prodeng-task
python -m venv .venv          # create a local virtual environment
source .venv/bin/activate     # Windows users can run `.venv\\Scripts\\activate`
make install                  # equivalent: pip install -e .[dev]
make seed                     # load sample conversations into SQLite
make dev                      # start uvicorn on http://127.0.0.1:8000
```

The seed script creates `autotag/app/data/autotag.db` and trains lightweight
models if they do not exist. Leave `make dev` running; it reloads when code
changes. Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

## Running the automated tests

```bash
make test          # runs pytest with the project's configuration
```

The same tests can be triggered manually with `pytest -q` once dependencies are
installed.

## Trying the API locally

With the server running (`make dev`), seed data loaded, and the virtual
environment active, open a second terminal and send the sample requests below to
see the end-to-end tagging flow:

```bash
curl -X POST localhost:8000/messages/ingest -H "content-type: application/json" \
  -d '{"conversation_id":"c1","text":"please top up my wallet","sender":"user"}'

curl -X POST localhost:8000/tickets/TK1/override -H "content-type: application/json" \
  -d '{"service_type":"wallet","category":"withdraw","reason":"agent correction"}'

curl -X GET localhost:8000/tickets
```

Inspect `GET /tickets` (or the Swagger UI) to confirm tickets and tags produced
by the hybrid rules + ML pipeline. Metrics and retraining utilities are exposed
under `/admin/*` routes.

## Docker workflow

```bash
make docker                                      # build the container image
# start the API (detach so we can run the seed script once the server is up)
docker run -d --name autotag -p 8000:8000 autotag:dev
# seed the database inside the running container
docker exec autotag python -m autotag.scripts.seed_db
```

The server now accepts requests on `http://127.0.0.1:8000`. When finished, stop
and clean up with `docker stop autotag && docker rm autotag`. For persistent
SQLite storage across runs, mount a volume to `/app/autotag/app/data`.

## Make targets

- `make install` – install the project in editable mode with dev extras.
- `make dev` – start the FastAPI app with Uvicorn reloader.
- `make seed` – populate the SQLite database with sample tickets/messages.
- `make retrain` – retrain the scikit-learn models on `autotag/app/data/sample_messages.jsonl`.
- `make test` – run the pytest suite.
- `make docker` – build the Docker image tagged `autotag:dev`.

## Confidence thresholds & rules tuning

Confidence bands are defined in `app/config.py` (`τ_high=0.80`, `τ_low=0.55`).
High-precision rules (marked `precision: high` in `app/data/rules.yaml`) force
confidence to ≥0.9. Adjust or add regex patterns in `rules.yaml` to capture new
keywords or markets.

Models live in `app/data/models/`. If absent, they are trained on startup using
the sample dataset. Explore metrics via `GET /admin/metrics`, and retrain models
with `POST /admin/retrain`. Ticket listings aggregate conversation history so
the tagging engine always evaluates the full thread when classifying.

## Assumptions

- You have Python 3.11+, `make`, and `curl` available in your shell (WSL is
  recommended for Windows users).
- Local developers run the seed script before exercising the API so the SQLite
  database and baseline ML models exist.
- Docker users run the seeding command inside the container (or mount a
  persistent volume) before sending requests.
- Networking is limited to localhost; no external services are required beyond
  the packages installed via `pip`.
