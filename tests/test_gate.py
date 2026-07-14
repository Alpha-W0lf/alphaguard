"""Gate policy + identity overwrite tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.ml.features import FeatureRow
from alphaguard.ml.gate import DownsideRiskGate, GateLoadError
from alphaguard.pipeline.service import PipelineService

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "data" / "fixtures" / "model_bundle_fixture"


@pytest.fixture(scope="module")
def gate() -> DownsideRiskGate:
    if not (BUNDLE / "manifest.json").exists():
        pytest.skip("fixture bundle missing — run `make bundle`")
    return DownsideRiskGate(BUNDLE)


def _row(**overrides: float) -> FeatureRow:
    values = {
        "finbert_sentiment": 0.1,
        "volatility_20d": 0.2,
        "return_5d_prior": 0.01,
        "return_20d_prior": 0.02,
        "spy_return_5d": 0.005,
    }
    values.update(overrides)
    return FeatureRow(
        event_id="evt-aapl-001",
        ticker="AAPL",
        values=values,
        feature_as_of=date(2024, 3, 11),
    )


def test_identity_overwrite() -> None:
    event = NewsEvent(
        event_id="evt-aapl-001",
        headline="x",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )
    proposal = Agent1Proposal(
        action="HOLD",
        confidence=0.5,
        rationale="wrong identity from llm",
        event_id="wrong-id",
        ticker="MSFT",
    )
    stamped = PipelineService.stamp_identity(proposal, event)
    assert stamped.event_id == "evt-aapl-001"
    assert stamped.ticker == "AAPL"


def test_hold_always_approve(gate: DownsideRiskGate) -> None:
    proposal = Agent1Proposal(
        action="HOLD",
        confidence=0.4,
        rationale="wait",
        event_id="evt-aapl-001",
        ticker="AAPL",
    )
    decision, reason = gate.apply_policy("HOLD", downside_risk_score=0.99, volatility_20d=0.9)
    assert decision == "approve"
    assert "HOLD" in reason


def test_pass_always_approve(gate: DownsideRiskGate) -> None:
    decision, _ = gate.apply_policy("PASS", downside_risk_score=0.99, volatility_20d=0.9)
    assert decision == "approve"


def test_buy_rejected_when_score_ge_threshold(gate: DownsideRiskGate) -> None:
    decision, reason = gate.apply_policy(
        "BUY",
        downside_risk_score=max(gate.manifest.score_threshold, 0.99),
        volatility_20d=0.1,
    )
    assert decision == "reject"
    assert "BUY rejected" in reason


def test_decide_deterministic(gate: DownsideRiskGate) -> None:
    proposal = Agent1Proposal(
        action="BUY",
        confidence=0.6,
        rationale="momentum",
        event_id="evt-aapl-001",
        ticker="AAPL",
    )
    row = _row()
    a = gate.decide(proposal, row)
    b = gate.decide(proposal, row)
    assert a.downside_risk_score == b.downside_risk_score
    assert a.decision == b.decision


def test_missing_manifest_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(GateLoadError):
        DownsideRiskGate(tmp_path)


def test_skewed_feature_names_fail_closed(tmp_path: Path, gate: DownsideRiskGate) -> None:
    import json

    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    manifest["feature_names"] = ["wrong_feature"]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "model.json").write_bytes((BUNDLE / "model.json").read_bytes())
    with pytest.raises(GateLoadError):
        DownsideRiskGate(tmp_path)
