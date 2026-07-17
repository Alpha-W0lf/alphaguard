"""Guide 07 — LangSmith fail-open adapter unit tests (mocked; no network)."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from alphaguard.config import Settings
from alphaguard.contracts.decisions import Agent2Decision
from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.obs.langsmith_adapter import emit_pipeline_run
from alphaguard.obs.summary import build_obs_status
from alphaguard.pipeline.service import PipelineService

ROOT = Path(__file__).resolve().parents[1]


def _settings(**overrides: Any) -> Settings:
    base = {
        "langsmith_tracing": False,
        "langsmith_api_key": None,
        "langsmith_project": "alphaguard-test",
        "phoenix_enabled": False,
        "artifacts_dir": ROOT / "artifacts",
        "fixtures_dir": ROOT / "data" / "fixtures",
        "model_bundle_dir": ROOT / "data" / "fixtures" / "model_bundle_fixture",
    }
    base.update(overrides)
    return Settings(**base)


def _ctx() -> dict[str, str]:
    return {
        "run_id": "run-test-001",
        "event_id": "evt-aapl-001",
        "ticker": "AAPL",
        "mode": "replay",
        "rag_mode": "fixture",
        "status": "success",
    }


def test_emit_skipped_when_tracing_off() -> None:
    factory = MagicMock()
    status, run_id = emit_pipeline_run(
        _settings(langsmith_tracing=False, langsmith_api_key="fake-key"),
        client_factory=factory,
        outputs={"action": "HOLD"},
        **_ctx(),
    )
    assert status == "skipped"
    assert run_id is None
    factory.assert_not_called()


def test_emit_skipped_when_key_empty() -> None:
    factory = MagicMock()
    status, run_id = emit_pipeline_run(
        _settings(langsmith_tracing=True, langsmith_api_key="   "),
        client_factory=factory,
        **_ctx(),
    )
    assert status == "skipped"
    assert run_id is None
    factory.assert_not_called()


def test_emit_ok_with_mock_client() -> None:
    client = MagicMock()
    factory = MagicMock(return_value=client)
    status, run_id = emit_pipeline_run(
        _settings(langsmith_tracing=True, langsmith_api_key="fake-key"),
        client_factory=factory,
        outputs={"action": "HOLD", "decision": "approve"},
        **_ctx(),
    )
    assert status == "ok"
    assert run_id is not None
    factory.assert_called_once()
    client.create_run.assert_called_once()
    client.update_run.assert_called_once()
    create_kwargs = client.create_run.call_args
    assert create_kwargs.args[0] == "alphaguard.pipeline.run"
    assert create_kwargs.args[2] == "chain"
    assert create_kwargs.kwargs["project_name"] == "alphaguard-test"


def test_emit_failed_when_client_raises() -> None:
    client = MagicMock()
    client.create_run.side_effect = RuntimeError("network down")
    factory = MagicMock(return_value=client)
    status, run_id = emit_pipeline_run(
        _settings(langsmith_tracing=True, langsmith_api_key="fake-key"),
        client_factory=factory,
        **_ctx(),
    )
    assert status == "failed"
    assert run_id is None


def test_build_obs_status_sets_run_id_on_ok() -> None:
    client = MagicMock()
    factory = MagicMock(return_value=client)
    obs, ls_id = build_obs_status(
        _settings(langsmith_tracing=True, langsmith_api_key="fake-key"),
        ROOT / "artifacts" / "runs" / "run-test-001.json",
        client_factory=factory,
        outputs={"action": "BUY"},
        **_ctx(),
    )
    assert obs.langsmith == "ok"
    assert obs.phoenix == "skipped"
    assert ls_id is not None


def test_pipeline_fail_open_degraded_on_langsmith_failed(tmp_path: Path) -> None:
    """Tracer failure must not flip gate decision; may degrade status."""
    fixtures = ROOT / "data" / "fixtures"
    settings = _settings(
        langsmith_tracing=True,
        langsmith_api_key="fake-key",
        artifacts_dir=tmp_path,
        fixtures_dir=fixtures,
        model_bundle_dir=fixtures / "model_bundle_fixture",
        alphaguard_rag_mode="fixture",
        alphaguard_mode="replay",
    )
    event = NewsEvent(
        event_id="evt-aapl-001",
        headline="Apple announces product",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )
    proposal = Agent1Proposal(
        action="HOLD",
        confidence=0.5,
        rationale="neutral fixture",
        event_id=event.event_id,
        ticker=event.ticker,
    )
    decision = Agent2Decision(
        event_id=event.event_id,
        ticker=event.ticker,
        action="HOLD",
        downside_risk_score=0.2,
        decision="approve",
        decision_reason="below_threshold",
        model_version="fixture",
        bundle_id="fixture",
        features_used=["finbert_sentiment"],
        feature_as_of=date(2024, 3, 11),
    )

    class _Analyst:
        def run(self, _event: NewsEvent, _hits: list[Any]) -> Agent1Proposal:
            return proposal

    class _Gate:
        def decide(self, _proposal: Agent1Proposal, _features: Any) -> Agent2Decision:
            return decision

    from unittest.mock import patch

    with patch(
        "alphaguard.obs.summary.emit_pipeline_run",
        return_value=("failed", None),
    ):
        svc = PipelineService(
            settings,
            analyst=_Analyst(),  # type: ignore[arg-type]
            gate=_Gate(),  # type: ignore[arg-type]
            skip_ollama_preflight=True,
        )
        envelope = svc.run(event)

    assert envelope.decision is not None
    assert envelope.decision.decision == "approve"
    assert envelope.obs.langsmith == "failed"
    assert envelope.status == "degraded"
    assert "langsmith_run_id" not in envelope.extras


def test_pipeline_ok_sets_extras_langsmith_run_id(tmp_path: Path) -> None:
    fixtures = ROOT / "data" / "fixtures"
    settings = _settings(
        langsmith_tracing=True,
        langsmith_api_key="fake-key",
        artifacts_dir=tmp_path,
        fixtures_dir=fixtures,
        model_bundle_dir=fixtures / "model_bundle_fixture",
        alphaguard_rag_mode="fixture",
        alphaguard_mode="replay",
    )
    event = NewsEvent(
        event_id="evt-aapl-001",
        headline="Apple announces product",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )
    proposal = Agent1Proposal(
        action="HOLD",
        confidence=0.5,
        rationale="neutral fixture",
        event_id=event.event_id,
        ticker=event.ticker,
    )
    decision = Agent2Decision(
        event_id=event.event_id,
        ticker=event.ticker,
        action="HOLD",
        downside_risk_score=0.2,
        decision="approve",
        decision_reason="below_threshold",
        model_version="fixture",
        bundle_id="fixture",
        features_used=["finbert_sentiment"],
        feature_as_of=date(2024, 3, 11),
    )

    class _Analyst:
        def run(self, _event: NewsEvent, _hits: list[Any]) -> Agent1Proposal:
            return proposal

    class _Gate:
        def decide(self, _proposal: Agent1Proposal, _features: Any) -> Agent2Decision:
            return decision

    from unittest.mock import patch

    with patch(
        "alphaguard.obs.summary.emit_pipeline_run",
        return_value=("ok", "ls-run-abc"),
    ):
        svc = PipelineService(
            settings,
            analyst=_Analyst(),  # type: ignore[arg-type]
            gate=_Gate(),  # type: ignore[arg-type]
            skip_ollama_preflight=True,
        )
        envelope = svc.run(event)

    assert envelope.obs.langsmith == "ok"
    assert envelope.status == "success"
    assert envelope.extras.get("langsmith_run_id") == "ls-run-abc"
    assert envelope.decision is not None
    assert envelope.decision.decision == "approve"


@pytest.mark.langsmith_live
def test_langsmith_live_optional() -> None:
    """Opt-in live probe — excluded by default addopts."""
    if os.environ.get("ALPHAGUARD_RUN_LANGSMITH_LIVE") != "1":
        pytest.skip("set ALPHAGUARD_RUN_LANGSMITH_LIVE=1 with real key")
    settings = Settings()
    if not settings.langsmith_tracing or not (settings.langsmith_api_key or "").strip():
        pytest.skip("LANGSMITH_TRACING + LANGSMITH_API_KEY required")
    status, run_id = emit_pipeline_run(
        settings,
        run_id="live-probe",
        event_id="live-evt",
        ticker="AAPL",
        mode="replay",
        rag_mode="fixture",
        status="success",
        outputs={"probe": True},
    )
    assert status == "ok"
    assert run_id is not None
