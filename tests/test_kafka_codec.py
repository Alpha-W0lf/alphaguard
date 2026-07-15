"""Unit tests for Kafka wire codec (Guide 04 D2)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from alphaguard.contracts.events import NewsEvent
from alphaguard.ingest.codec import CodecError, deserialize_bytes, deserialize_payload, serialize_event

HAPPY_EVENT = NewsEvent(
    event_id="evt-aapl-001",
    headline="Apple announces record iPhone demand in key markets",
    ticker="AAPL",
    source="fixture",
    published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
)


def test_codec_roundtrip_happy_path() -> None:
    raw = serialize_event(HAPPY_EVENT)
    event = deserialize_bytes(raw)
    assert event.event_id == HAPPY_EVENT.event_id
    assert event.ticker == "AAPL"


@pytest.mark.parametrize(
    ("case_id", "payload"),
    [
        ("poison_bad_payload_version", {"payload_version": "2", "event_id": "e1", "headline": "x", "ticker": "AAPL", "source": "fixture", "published_at": "2024-03-12T14:30:00+00:00"}),
        ("poison_oou_ticker", {"payload_version": "1", "event_id": "e1", "headline": "Tesla news", "ticker": "TSLA", "source": "fixture", "published_at": "2024-03-12T14:30:00+00:00"}),
        ("poison_missing_headline", {"payload_version": "1", "event_id": "e1", "ticker": "AAPL", "source": "fixture", "published_at": "2024-03-12T14:30:00+00:00"}),
    ],
    ids=["poison_bad_payload_version", "poison_oou_ticker", "poison_missing_headline"],
)
def test_codec_rejects_frozen_poison_examples(case_id: str, payload: dict) -> None:
    del case_id
    with pytest.raises(CodecError):
        deserialize_payload(payload)
