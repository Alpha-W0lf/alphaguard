"""Unit tests for RSS poll orchestration (Guide 06 Phase C) — no live Kafka."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from alphaguard.contracts.events import NewsEvent, OutOfUniverseTickerError
from alphaguard.ingest.producer import KafkaProduceError
from alphaguard.ingest.rss_fetch import RssFetchError
from alphaguard.ingest.rss_normalize import NormalizeResult, normalize_rss_xml
from alphaguard.ingest.rss_poll import (
    exit_code_for_summary,
    poll_once,
    resolve_tickers,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "rss" / "yahoo_aapl_sample.xml"


class _FakeProducer:
    def __init__(self, *, fail_on: int | None = None) -> None:
        self.sent: list[NewsEvent] = []
        self._fail_on = fail_on

    # produce_event calls producer.send(...).get — we patch produce_event instead


def test_resolve_tickers_all_and_oou() -> None:
    all_t = resolve_tickers("all")
    assert "AAPL" in all_t
    assert len(all_t) == 8
    with pytest.raises(OutOfUniverseTickerError):
        resolve_tickers("TSLA")


def test_poll_once_rejects_non_positive_max_items() -> None:
    with pytest.raises(ValueError, match="max_items"):
        poll_once(
            ["AAPL"],
            producer=object(),  # type: ignore[arg-type]
            max_items=0,
            fetch_fn=lambda t: b"",
            normalize_fn=normalize_rss_xml,
        )


def test_poll_once_produces_capped_items(monkeypatch: pytest.MonkeyPatch) -> None:
    xml = FIXTURE.read_bytes()
    produced: list[NewsEvent] = []

    def fake_produce(producer: Any, event: NewsEvent, **kwargs: Any) -> dict[str, Any]:
        produced.append(event)
        return {"ok": True, "event_id": event.event_id}

    monkeypatch.setattr("alphaguard.ingest.rss_poll.produce_event", fake_produce)
    summary = poll_once(
        ["AAPL"],
        producer=object(),  # type: ignore[arg-type]
        max_items=2,
        fetch_fn=lambda t: xml,
        normalize_fn=normalize_rss_xml,
    )
    assert summary.ok
    assert summary.fetched == 1
    assert summary.produced == 2
    assert summary.skipped_items == 1
    assert len(produced) == 2
    assert exit_code_for_summary(summary) == 0


def test_poll_empty_feed_exit_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = b"""<?xml version="1.0"?><rss version="2.0"><channel>
    <title>empty</title></channel></rss>"""
    monkeypatch.setattr(
        "alphaguard.ingest.rss_poll.produce_event",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not produce")),
    )
    summary = poll_once(
        ["AAPL"],
        producer=object(),  # type: ignore[arg-type]
        fetch_fn=lambda t: empty,
        normalize_fn=normalize_rss_xml,
    )
    assert summary.ok
    assert summary.produced == 0
    assert exit_code_for_summary(summary) == 0


def test_poll_partial_multi_ticker(monkeypatch: pytest.MonkeyPatch) -> None:
    xml = FIXTURE.read_bytes()
    produced: list[str] = []

    def fake_produce(producer: Any, event: NewsEvent, **kwargs: Any) -> dict[str, Any]:
        produced.append(event.ticker)
        return {"ok": True}

    def fetch_fn(ticker: str) -> bytes:
        if ticker == "MSFT":
            raise RssFetchError("boom")
        return xml

    monkeypatch.setattr("alphaguard.ingest.rss_poll.produce_event", fake_produce)
    summary = poll_once(
        ["AAPL", "MSFT"],
        producer=object(),  # type: ignore[arg-type]
        max_items=1,
        fetch_fn=fetch_fn,
        normalize_fn=normalize_rss_xml,
    )
    assert not summary.ok
    assert summary.produced == 1
    assert any("MSFT" in e for e in summary.errors)
    assert exit_code_for_summary(summary) == 1


def test_poll_kafka_produce_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    xml = FIXTURE.read_bytes()

    def fail_produce(producer: Any, event: NewsEvent, **kwargs: Any) -> dict[str, Any]:
        raise KafkaProduceError("kafka down")

    monkeypatch.setattr("alphaguard.ingest.rss_poll.produce_event", fail_produce)
    summary = poll_once(
        ["AAPL"],
        producer=object(),  # type: ignore[arg-type]
        max_items=1,
        fetch_fn=lambda t: xml,
        normalize_fn=normalize_rss_xml,
    )
    assert exit_code_for_summary(summary) == 1
    assert summary.produced == 0
