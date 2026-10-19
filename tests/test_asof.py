"""As-of RetrievalHit filtering (AG3)."""

from __future__ import annotations

from datetime import datetime, timezone

from alphaguard.contracts.retrieval import RetrievalHit
from alphaguard.rag.asof import filter_hits_as_of


def test_future_available_at_dropped() -> None:
    published = datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc)
    hits = [
        RetrievalHit(
            document_id="past",
            text="ok",
            ticker="AAPL",
            available_at=datetime(2024, 3, 12, 13, 0, tzinfo=timezone.utc),
            source="fixture",
            score=0.5,
        ),
        RetrievalHit(
            document_id="future",
            text="leak",
            ticker="AAPL",
            available_at=datetime(2024, 3, 13, 12, 0, tzinfo=timezone.utc),
            source="fixture",
            score=0.99,
        ),
    ]
    filtered = filter_hits_as_of(hits, published)
    assert [h.document_id for h in filtered] == ["past"]
