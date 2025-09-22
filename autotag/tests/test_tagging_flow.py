from __future__ import annotations

from fastapi.testclient import TestClient

from autotag.app.main import app
from autotag.app.services import confidence_policy


def test_ingest_auto_tags() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/messages/ingest",
            json={
                "conversation_id": "conv_auto",
                "text": "please top up my wallet asap",
                "sender": "user",
            },
        )
        payload = response.json()
        assert response.status_code == 200
        assert payload["source"] in {"rule", "ml"}
        assert payload["clarifier_question"] is None
        assert payload["suggested_tags"]["service_type"] == "wallet"
        assert payload["suggested_tags"]["category"] == "top_up"


def test_ingest_routes_to_llm(monkeypatch) -> None:
    def fake_evaluate(rule_result, ml_result):  # type: ignore[unused-argument]
        return {
            "service_type": "wallet",
            "category": "withdraw",
            "confidence": 0.6,
            "action": "llm",
            "source": "ml",
        }

    with TestClient(app) as client:
        monkeypatch.setattr(confidence_policy, "evaluate", fake_evaluate)
        response = client.post(
            "/messages/ingest",
            json={
                "conversation_id": "conv_llm",
                "text": "maybe let me withdraw from the wallet",
                "sender": "user",
            },
        )
        payload = response.json()
        assert response.status_code == 200
        assert payload["source"] == "llm"
        assert payload["clarifier_question"] is None
        assert payload["suggested_tags"]["category"] == "withdraw"


def test_ticket_listing_and_conversation_context() -> None:
    with TestClient(app) as client:
        first = client.post(
            "/messages/ingest",
            json={
                "conversation_id": "conv_thread",
                "text": "please top up my wallet with some funds",
                "sender": "user",
            },
        )
        assert first.status_code == 200
        ticket_id = first.json()["ticket_id"]

        second = client.post(
            "/messages/ingest",
            json={
                "conversation_id": "conv_thread",
                "text": "any update on that request?",
                "sender": "user",
            },
        )
        assert second.status_code == 200
        payload = second.json()

        assert payload["ticket_id"] == ticket_id
        assert payload["suggested_tags"]["service_type"] == "wallet"
        assert payload["suggested_tags"]["category"] == "top_up"

        listing = client.get("/tickets")
        assert listing.status_code == 200
        tickets = listing.json()
        thread_entry = next(t for t in tickets if t["ticket_id"] == ticket_id)
        assert thread_entry["message_count"] == 2
        assert thread_entry["last_message_preview"]

        detail = client.get(f"/tickets/{ticket_id}")
        assert detail.status_code == 200
        assert len(detail.json()["messages"]) == 2
