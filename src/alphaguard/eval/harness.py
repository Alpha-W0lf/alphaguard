"""Thin golden executors — real façades, frozen expect protocol (Guide 03)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from alphaguard.contracts.events import NewsEvent, OutOfUniverseTickerError
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.contracts.retrieval import RetrievalHit
from alphaguard.ingest.replay import FixtureLoadError, load_replay_events
from alphaguard.ml.gate import DownsideRiskGate
from alphaguard.pipeline.service import PipelineService
from alphaguard.rag.asof import filter_hits_as_of

FORCE_SCORE_EPSILON = 1e-6
DEFAULT_PUBLISHED = "2024-03-12T14:30:00Z"


def resolve_force_score(force_score: float | str, threshold: float) -> float:
    """Resolve boundary sentinels from live manifest threshold (never hardcode 0.45)."""
    if isinstance(force_score, str):
        if force_score == "eq_threshold":
            return float(threshold)
        if force_score == "just_below_threshold":
            return float(threshold) - FORCE_SCORE_EPSILON
        raise ValueError(f"unknown force_score sentinel: {force_score!r}")
    return float(force_score)


def build_vol_veto_gate(fixture_bundle: Path, tmp_dir: Path) -> DownsideRiskGate:
    """Copy fixture bundle into tmp_dir and enable vol veto on the TMP manifest only."""
    shutil.copy(fixture_bundle / "manifest.json", tmp_dir / "manifest.json")
    shutil.copy(fixture_bundle / "model.json", tmp_dir / "model.json")
    manifest = json.loads((tmp_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest["vol_veto_enabled"] = True
    manifest["vol_veto_threshold"] = 0.05
    (tmp_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return DownsideRiskGate(tmp_dir)


def execute_golden(
    case: dict[str, Any],
    *,
    gate: DownsideRiskGate,
    fixture_bundle: Path,
    tmp_path: Path,
) -> None:
    """Run one golden against the façade named by ``check``; assert frozen expect."""
    check = case["check"]
    expect = case["expect"]
    if check == "schema":
        _run_schema(case, expect)
    elif check == "identity":
        _run_identity(case, expect)
    elif check == "asof":
        _run_asof(case, expect)
    elif check == "gate":
        active = gate
        if case.get("tmp_vol_veto") or case.get("case_id") == "gate_vol_veto_reject":
            veto_dir = tmp_path / case["case_id"]
            veto_dir.mkdir(parents=True, exist_ok=True)
            active = build_vol_veto_gate(fixture_bundle, veto_dir)
        _run_gate(case, expect, active)
    elif check == "oou":
        _run_oou(case, expect, tmp_path)
    else:
        raise AssertionError(f"unhandled check={check!r}")


def _run_schema(case: dict[str, Any], expect: str) -> None:
    model_name = case.get("model", "Agent1Proposal")
    if model_name == "Agent1Proposal":
        payload = {
            "action": case["action"],
            "confidence": case["confidence"],
            "rationale": case.get("rationale", "golden"),
            "event_id": case.get("event_id", "evt-golden"),
            "ticker": case.get("ticker", "AAPL"),
        }
        model_cls: type = Agent1Proposal
    elif model_name == "NewsEvent":
        payload = {
            "event_id": case.get("event_id", "evt-golden"),
            "headline": case.get("headline", "golden"),
            "ticker": case.get("ticker", case["action"]),
            "source": case.get("source", "fixture"),
            "published_at": case.get("published_at", DEFAULT_PUBLISHED),
        }
        model_cls = NewsEvent
    elif model_name == "RetrievalHit":
        payload = {
            "document_id": case.get("document_id", "doc-golden"),
            "text": case.get("text", "golden"),
            "ticker": case.get("ticker", "AAPL"),
            "available_at": case.get("available_at", DEFAULT_PUBLISHED),
            "source": case.get("source", "fixture"),
            "score": case.get("score", 0.0),
        }
        model_cls = RetrievalHit
    else:
        raise AssertionError(f"unknown schema model={model_name!r}")

    if expect == "ok":
        model_cls.model_validate(payload)
        return
    if expect == "reject":
        try:
            model_cls.model_validate(payload)
        except (ValidationError, OutOfUniverseTickerError, ValueError, TypeError):
            return
        raise AssertionError(f"schema expected reject for {case['case_id']}")
    raise AssertionError(f"unknown schema expect={expect!r}")


def _run_identity(case: dict[str, Any], expect: str) -> None:
    proposal = Agent1Proposal(
        action="HOLD",
        confidence=0.5,
        rationale="golden",
        event_id=case["llm_event_id"],
        ticker=case["llm_ticker"],
    )
    event = NewsEvent(
        event_id=case["input_event_id"],
        headline="golden",
        ticker=case["input_ticker"],
        source="fixture",
        published_at=datetime.fromisoformat(DEFAULT_PUBLISHED.replace("Z", "+00:00")),
    )
    stamped = PipelineService.stamp_identity(proposal, event)
    if expect != "stamped_from_input":
        raise AssertionError(f"unknown identity expect={expect!r}")
    assert stamped.ticker == case["input_ticker"]
    assert stamped.event_id == case["input_event_id"]


def _run_asof(case: dict[str, Any], expect: str) -> None:
    published = datetime.fromisoformat(
        str(case["published_at"]).replace("Z", "+00:00")
    )
    hits = [
        RetrievalHit.model_validate(
            {
                "document_id": h["document_id"],
                "text": h.get("text", "golden"),
                "ticker": h.get("ticker", "AAPL"),
                "available_at": h["available_at"],
                "source": h.get("source", "fixture"),
                "score": h.get("score", 0.0),
            }
        )
        for h in case["hits"]
    ]
    filtered = filter_hits_as_of(hits, published)
    if expect == "future_hit_dropped":
        assert all(h.available_at <= published for h in filtered)
        if any(h.available_at > published for h in hits) and any(
            h.available_at <= published for h in hits
        ):
            assert len(filtered) >= 1
        return
    if expect == "kept":
        assert len(filtered) == len(hits)
        assert sorted(h.document_id for h in filtered) == sorted(
            h.document_id for h in hits
        )
        return
    if expect == "empty":
        assert len(filtered) == 0
        return
    raise AssertionError(f"unknown asof expect={expect!r}")


def _run_gate(case: dict[str, Any], expect: str, gate: DownsideRiskGate) -> None:
    score = resolve_force_score(case["force_score"], gate.manifest.score_threshold)
    vol = float(case.get("volatility_20d", 0.1))
    action = case["action"]
    if expect == "same_decision":
        a = gate.apply_policy(action, downside_risk_score=score, volatility_20d=vol)
        b = gate.apply_policy(action, downside_risk_score=score, volatility_20d=vol)
        assert a == b
        return
    if expect in ("approve", "reject"):
        decision, _reason = gate.apply_policy(
            action, downside_risk_score=score, volatility_20d=vol
        )
        assert decision == expect
        return
    raise AssertionError(f"unknown gate expect={expect!r}")


def _run_oou(case: dict[str, Any], expect: str, tmp_path: Path) -> None:
    if expect != "reject":
        raise AssertionError(f"unknown oou expect={expect!r}")
    via = case.get("via", "news_event")
    ticker = case["ticker"]
    if via == "fixture":
        path = tmp_path / f"{case['case_id']}.jsonl"
        path.write_text(
            json.dumps(
                {
                    "event_id": "evt-oou-fixture",
                    "headline": "OOU fixture golden",
                    "ticker": ticker,
                    "source": "fixture",
                    "published_at": DEFAULT_PUBLISHED,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            load_replay_events(path)
        except (FixtureLoadError, OutOfUniverseTickerError, ValidationError):
            return
        raise AssertionError(f"fixture OOU expected reject for {case['case_id']}")
    try:
        NewsEvent.model_validate(
            {
                "event_id": "evt-oou",
                "headline": "OOU golden",
                "ticker": ticker,
                "source": "fixture",
                "published_at": DEFAULT_PUBLISHED,
            }
        )
    except (ValidationError, OutOfUniverseTickerError, ValueError):
        return
    raise AssertionError(f"NewsEvent OOU expected reject for {case['case_id']}")
