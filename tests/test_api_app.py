"""FastAPI characterization tests for /health, /replay, and /trigger (JH-63.10)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from alphaguard.api.app import create_app
from alphaguard.config import Settings
from alphaguard.infra.preflight import PreflightError


@pytest.fixture
def client_fixture_mode(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("ALPHAGUARD_ANALYST_MODE", "fixture")
    monkeypatch.setenv("ALPHAGUARD_MODE", "replay")
    monkeypatch.setenv("ALPHAGUARD_RAG_MODE", "fixture")
    app = create_app()
    return TestClient(app)


def test_health_endpoint_fixture_mode(client_fixture_mode: TestClient) -> None:
    response = client_fixture_mode.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["resource_mode"] == "replay_fixture"
    dep_names = {d["name"]: d["status"] for d in data["dependencies"]}
    assert dep_names["app"] == "ok"
    assert dep_names["kafka"] == "skipped"
    assert dep_names["qdrant"] == "skipped"
    assert dep_names["ollama"] == "skipped"


def test_health_endpoint_ollama_unreachable_degrades() -> None:
    with patch("alphaguard.api.app.preflight_ollama", side_effect=PreflightError("Ollama unreachable")):
        settings = Settings(alphaguard_analyst_mode="ollama")
        with patch("alphaguard.api.app.get_settings", return_value=settings):
            app = create_app()
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            dep_names = {d["name"]: d["status"] for d in data["dependencies"]}
            assert dep_names["ollama"] == "error"


def test_replay_endpoint_with_fixture_analyst(client_fixture_mode: TestClient) -> None:
    response = client_fixture_mode.post(
        "/replay",
        json={"event_id": "evt-aapl-001", "fixture_analyst": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event_id"] == "evt-aapl-001"
    assert data["ticker"] == "AAPL"
    assert data["proposal"]["action"] == "BUY"
    assert data["decision"]["decision"] == "reject"
    assert "score_threshold" in data["decision"]["decision_reason"]
    assert "artifacts/runs" in data["obs"]["local_summary_path"]


def test_replay_endpoint_unknown_event_returns_404(client_fixture_mode: TestClient) -> None:
    response = client_fixture_mode.post(
        "/replay",
        json={"event_id": "evt-unknown-999", "fixture_analyst": True},
    )
    assert response.status_code == 404


def test_trigger_bad_payload_version(client_fixture_mode: TestClient) -> None:
    response = client_fixture_mode.post(
        "/trigger",
        json={
            "payload_version": "2",
            "event_id": "evt-1",
            "headline": "Sample headline",
            "ticker": "AAPL",
            "source": "fixture",
            "published_at": "2024-03-12T14:30:00Z",
        },
    )
    assert response.status_code == 400
    assert "unsupported payload_version" in response.text


def test_trigger_kafka_unavailable_returns_503(client_fixture_mode: TestClient) -> None:
    # Kafka is not running, so probe_kafka fails fast
    with patch("alphaguard.api.app.probe_kafka", return_value=("error", "connection refused")):
        response = client_fixture_mode.post(
            "/trigger",
            json={
                "payload_version": "1",
                "event_id": "evt-1",
                "headline": "Sample headline",
                "ticker": "AAPL",
                "source": "fixture",
                "published_at": "2024-03-12T14:30:00Z",
            },
        )
        assert response.status_code == 503
        assert "kafka unavailable" in response.text
