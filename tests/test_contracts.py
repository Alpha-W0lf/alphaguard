"""Contract validation tests (ARCHITECTURE §7)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from alphaguard.contracts.events import NewsEvent, OutOfUniverseTickerError
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.contracts.retrieval import RetrievalHit


def test_news_event_valid() -> None:
    event = NewsEvent(
        event_id="e1",
        headline="Apple rises",
        ticker="aapl",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )
    assert event.ticker == "AAPL"


def test_empty_headline_rejected() -> None:
    with pytest.raises(ValidationError):
        NewsEvent(
            event_id="e1",
            headline="   ",
            ticker="AAPL",
            source="fixture",
            published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
        )


def test_oou_ticker_rejected() -> None:
    # Pydantic wraps validator ValueError into ValidationError; message must stay fail-closed.
    with pytest.raises((OutOfUniverseTickerError, ValidationError)) as exc_info:
        NewsEvent(
            event_id="e1",
            headline="Tesla news",
            ticker="TSLA",
            source="fixture",
            published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
        )
    assert "out of universe" in str(exc_info.value).lower() or "TSLA" in str(exc_info.value)


def test_sell_rejected() -> None:
    with pytest.raises(ValidationError):
        Agent1Proposal(
            action="SELL",  # type: ignore[arg-type]
            confidence=0.5,
            rationale="short",
            event_id="e1",
            ticker="AAPL",
        )


def test_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        Agent1Proposal(
            action="BUY",
            confidence=1.5,
            rationale="too confident",
            event_id="e1",
            ticker="AAPL",
        )


def test_confidence_string_rejected() -> None:
    with pytest.raises(ValidationError):
        Agent1Proposal.model_validate(
            {
                "action": "BUY",
                "confidence": "0.8",
                "rationale": "string confidence",
                "event_id": "e1",
                "ticker": "AAPL",
            }
        )


def test_retrieval_hit_requires_aware_available_at() -> None:
    with pytest.raises(ValidationError):
        RetrievalHit(
            document_id="d1",
            text="x",
            ticker="AAPL",
            available_at=datetime(2024, 3, 12, 12, 0),  # naive
            source="fixture",
            score=0.1,
        )
