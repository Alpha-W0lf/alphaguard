"""Fixture load + OOU rejection."""

from __future__ import annotations

from pathlib import Path

import pytest

from alphaguard.ingest.replay import FixtureLoadError, load_replay_events
from alphaguard.rag.fixture import load_fixture_hits

ROOT = Path(__file__).resolve().parents[1]


def test_load_replay_events() -> None:
    events = load_replay_events(ROOT / "data" / "fixtures" / "replay_events.jsonl")
    assert len(events) >= 5
    tickers = {e.ticker for e in events}
    assert len(tickers) >= 3


def test_fixture_sidecar_drops_future_hit() -> None:
    events = load_replay_events(ROOT / "data" / "fixtures" / "replay_events.jsonl")
    event = next(e for e in events if e.event_id == "evt-aapl-001")
    hits = load_fixture_hits(
        event,
        ROOT / "data" / "fixtures" / "retrieval_hits.json",
        top_k=5,
    )
    assert all(h.available_at <= event.published_at for h in hits)
    assert "doc-aapl-future-leak" not in {h.document_id for h in hits}


def test_oou_line_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"event_id":"x","headline":"Tesla","ticker":"TSLA","source":"fixture",'
        '"published_at":"2024-03-12T14:30:00Z"}\n',
        encoding="utf-8",
    )
    with pytest.raises(FixtureLoadError):
        load_replay_events(path)


def test_missing_fixture_file(tmp_path: Path) -> None:
    with pytest.raises(FixtureLoadError):
        load_replay_events(tmp_path / "missing.jsonl")
