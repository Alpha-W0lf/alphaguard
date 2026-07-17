"""Unit tests for RSS normalize (Guide 06 Phase A) — offline fixtures only."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from alphaguard.contracts.events import OutOfUniverseTickerError
from alphaguard.ingest.codec import deserialize_bytes, serialize_event
from alphaguard.ingest.rss_normalize import (
    RssParseError,
    make_rss_event_id,
    normalize_rss_xml,
    require_universe_ticker,
    stable_item_key,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "rss" / "yahoo_aapl_sample.xml"


def test_require_universe_rejects_oou() -> None:
    with pytest.raises(OutOfUniverseTickerError):
        require_universe_ticker("TSLA")


def test_normalize_happy_and_skips_malformed() -> None:
    raw = FIXTURE.read_bytes()
    result = normalize_rss_xml(raw, "AAPL")
    assert len(result.events) == 3
    assert result.skipped_items == 1
    assert all(e.source == "rss" for e in result.events)
    assert all(e.ticker == "AAPL" for e in result.events)
    assert all(e.published_at.tzinfo is not None for e in result.events)


def test_event_id_stable_for_same_guid() -> None:
    key = stable_item_key(
        guid="yahoo-guid-aapl-001",
        link="https://example.com/a",
        title="t",
        published_at=datetime(2026, 7, 14, 15, 30, tzinfo=timezone.utc),
    )
    a = make_rss_event_id("AAPL", key)
    b = make_rss_event_id("AAPL", key)
    assert a == b
    other = make_rss_event_id("AAPL", "yahoo-guid-aapl-002")
    assert a != other


def test_normalize_same_guid_stable_across_calls() -> None:
    raw = FIXTURE.read_bytes()
    first = normalize_rss_xml(raw, "aapl").events[0]
    second = normalize_rss_xml(raw, "AAPL").events[0]
    assert first.event_id == second.event_id
    assert first.event_id == make_rss_event_id("AAPL", "yahoo-guid-aapl-001")


def test_codec_round_trip() -> None:
    raw = FIXTURE.read_bytes()
    event = normalize_rss_xml(raw, "AAPL").events[0]
    wire = serialize_event(event)
    back = deserialize_bytes(wire)
    assert back.event_id == event.event_id
    assert back.headline == event.headline
    assert back.source == "rss"
    assert back.ticker == "AAPL"


def test_html_body_fails_closed() -> None:
    with pytest.raises(RssParseError):
        normalize_rss_xml(b"<html><body>not rss</body></html>", "AAPL")


def test_empty_channel() -> None:
    xml = b"""<?xml version="1.0"?><rss version="2.0"><channel>
    <title>empty</title></channel></rss>"""
    result = normalize_rss_xml(xml, "AAPL")
    assert result.events == []
    assert result.skipped_items == 0
