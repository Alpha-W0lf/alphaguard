"""Guide 08 — Phoenix fail-open adapter unit tests (mocked; no network)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from alphaguard.config import Settings
from alphaguard.contracts.decisions import Agent2Decision
from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.obs.phoenix_adapter import emit_pipeline_span
from alphaguard.obs.summary import build_obs_status
from alphaguard.pipeline.service import PipelineService

ROOT = Path(__file__).resolve().parents[1]


def _settings(**overrides: Any) -> Settings:
    base = {
        "langsmith_tracing": False,
        "langsmith_api_key": None,
        "phoenix_enabled": False,
        "artifacts_dir": ROOT / "artifacts",
        "fixtures_dir": ROOT / "data" / "fixtures",
        "model_bundle_dir": ROOT / "data" / "fixtures" / "model_bundle_fixture",
    }
    base.update(overrides)
    return Settings(**base)


def _ctx() -> dict[str, str]:
    return {
        "run_id": "run-test-px-001",
        "event_id": "evt-aapl-001",
        "ticker": "AAPL",
        "mode": "replay",
        "rag_mode": "fixture",
        "status": "success",
    }


def _mock_tracer_factory(*, flush_ok: bool = True, raise_on_span: bool = False):
    span = MagicMock()
    span.get_span_context.return_value = MagicMock(span_id=0xABCDEF0123456789)
    span.set_input = MagicMock()
    span.set_output = MagicMock()

    @contextmanager
    def _span_cm(*_a: Any, **_k: Any):
        if raise_on_span:
            raise RuntimeError("span boom")
        yield span

    tracer = MagicMock()
    tracer.start_as_current_span.side_effect = _span_cm
    provider = MagicMock()
    provider.force_flush.return_value = flush_ok
    factory = MagicMock(return_value=(tracer, provider))
    return factory, tracer, provider, span


def test_emit_skipped_when_phoenix_off() -> None:
    factory = MagicMock()
    status, span_id = emit_pipeline_span(
        _settings(phoenix_enabled=False),
        tracer_factory=factory,
        outputs={"action": "HOLD"},
        **_ctx(),
    )
    assert status == "skipped"
    assert span_id is None
    factory.assert_not_called()


def test_emit_ok_with_mock_tracer() -> None:
    factory, tracer, provider, _span = _mock_tracer_factory()
    status, span_id = emit_pipeline_span(
        _settings(phoenix_enabled=True),
        tracer_factory=factory,
        outputs={"action": "HOLD", "decision": "approve"},
        **_ctx(),
    )
    assert status == "ok"
    assert span_id == "abcdef0123456789"
    factory.assert_called_once()
    tracer.start_as_current_span.assert_called_once()
    call_kwargs = tracer.start_as_current_span.call_args.kwargs
    assert call_kwargs.get("openinference_span_kind") == "chain"
    provider.force_flush.assert_called_once()


def test_emit_failed_when_tracer_raises() -> None:
    factory, _tracer, _provider, _span = _mock_tracer_factory(raise_on_span=True)
    status, span_id = emit_pipeline_span(
        _settings(phoenix_enabled=True),
        tracer_factory=factory,
        **_ctx(),
    )
    assert status == "failed"
    assert span_id is None


def test_emit_failed_when_force_flush_false() -> None:
    factory, _tracer, provider, _span = _mock_tracer_factory(flush_ok=False)
    status, span_id = emit_pipeline_span(
        _settings(phoenix_enabled=True),
        tracer_factory=factory,
        **_ctx(),
    )
    assert status == "failed"
    assert span_id is None
    provider.force_flush.assert_called_once()


def test_build_obs_status_sets_phoenix_span_id_on_ok() -> None:
    factory, _tracer, _provider, _span = _mock_tracer_factory()
    obs, ls_id, px_id = build_obs_status(
        _settings(phoenix_enabled=True),
        ROOT / "artifacts" / "runs" / "run-test-px-001.json",
        tracer_factory=factory,
        outputs={"action": "BUY"},
        **_ctx(),
    )
    assert obs.phoenix == "ok"
    assert obs.langsmith == "skipped"
    assert ls_id is None
    assert px_id == "abcdef0123456789"


def _fixture_pipeline_event() -> tuple[NewsEvent, Agent1Proposal, Agent2Decision]:
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
    return event, proposal, decision


def test_pipeline_fail_open_degraded_on_phoenix_failed(tmp_path: Path) -> None:
    fixtures = ROOT / "data" / "fixtures"
    settings = _settings(
        phoenix_enabled=True,
        artifacts_dir=tmp_path,
        fixtures_dir=fixtures,
        model_bundle_dir=fixtures / "model_bundle_fixture",
        alphaguard_rag_mode="fixture",
        alphaguard_mode="replay",
    )
    event, proposal, decision = _fixture_pipeline_event()

    class _Analyst:
        def run(self, _event: NewsEvent, _hits: list[Any]) -> Agent1Proposal:
            return proposal

    class _Gate:
        def decide(self, _proposal: Agent1Proposal, _features: Any) -> Agent2Decision:
            return decision

    with patch(
        "alphaguard.obs.summary.emit_pipeline_span",
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
    assert envelope.obs.phoenix == "failed"
    assert envelope.status == "degraded"
    assert "phoenix_span_id" not in envelope.extras


def test_pipeline_ok_sets_extras_phoenix_span_id(tmp_path: Path) -> None:
    fixtures = ROOT / "data" / "fixtures"
    settings = _settings(
        phoenix_enabled=True,
        artifacts_dir=tmp_path,
        fixtures_dir=fixtures,
        model_bundle_dir=fixtures / "model_bundle_fixture",
        alphaguard_rag_mode="fixture",
        alphaguard_mode="replay",
    )
    event, proposal, decision = _fixture_pipeline_event()

    class _Analyst:
        def run(self, _event: NewsEvent, _hits: list[Any]) -> Agent1Proposal:
            return proposal

    class _Gate:
        def decide(self, _proposal: Agent1Proposal, _features: Any) -> Agent2Decision:
            return decision

    with patch(
        "alphaguard.obs.summary.emit_pipeline_span",
        return_value=("ok", "abcdef0123456789"),
    ):
        svc = PipelineService(
            settings,
            analyst=_Analyst(),  # type: ignore[arg-type]
            gate=_Gate(),  # type: ignore[arg-type]
            skip_ollama_preflight=True,
        )
        envelope = svc.run(event)

    assert envelope.obs.phoenix == "ok"
    assert envelope.status == "success"
    assert envelope.extras.get("phoenix_span_id") == "abcdef0123456789"
    assert envelope.decision is not None
    assert envelope.decision.decision == "approve"


@pytest.mark.phoenix_live
def test_phoenix_live_optional() -> None:
    """Opt-in live probe — excluded by default addopts."""
    if os.environ.get("ALPHAGUARD_RUN_PHOENIX_LIVE") != "1":
        pytest.skip("set ALPHAGUARD_RUN_PHOENIX_LIVE=1 with Phoenix collector up")
    settings = Settings()
    if not settings.phoenix_enabled:
        pytest.skip("PHOENIX_ENABLED=true required")
    status, span_id = emit_pipeline_span(
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
    assert span_id is not None
