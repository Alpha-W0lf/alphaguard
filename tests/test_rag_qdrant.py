"""Qdrant retrieval against an in-memory client (no Docker, no Torch)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from alphaguard.contracts.events import NewsEvent
from alphaguard.rag import service

T0 = datetime(2026, 1, 5, 15, 0, tzinfo=timezone.utc)


def _fake_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic 384-d vectors; identical text gives an identical vector."""
    out = []
    for text in texts:
        digest = hashlib.sha256(text.encode()).digest()
        out.append([(digest[i % 32] + 1) / 256.0 for i in range(384)])
    return out


def _event(event_id: str, headline: str, minutes: int, ticker: str = "AAPL") -> NewsEvent:
    return NewsEvent(
        event_id=event_id,
        headline=headline,
        ticker=ticker,
        source="fixture",
        published_at=T0 + timedelta(minutes=minutes),
    )


@pytest.fixture
def rag(monkeypatch: pytest.MonkeyPatch) -> service.QdrantRag:
    monkeypatch.setattr(service, "_embed", _fake_embed)
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="news",
        vectors_config=qm.VectorParams(size=384, distance=qm.Distance.COSINE),
    )
    rag = service.QdrantRag(url=":memory:", collection="news")
    rag._client = client
    return rag


def test_query_returns_earlier_same_ticker_context(rag: service.QdrantRag) -> None:
    rag.upsert_event(_event("evt-old-1", "Apple supplier cuts guidance", -120))
    rag.upsert_event(_event("evt-old-2", "Apple faces EU antitrust probe", -60))
    rag.upsert_event(_event("evt-msft", "Microsoft beats estimates", -30, ticker="MSFT"))
    rag.upsert_event(_event("evt-future", "Apple recalls devices", 60))

    hits = rag.query(_event("evt-now", "Apple shares slide on demand worries", 0), top_k=5)

    ids = {h.document_id for h in hits}
    assert ids == {"evt-old-1", "evt-old-2"}
    assert all(h.source == "qdrant" for h in hits)


def test_query_never_returns_the_event_itself(rag: service.QdrantRag) -> None:
    rag.upsert_event(_event("evt-old-1", "Apple supplier cuts guidance", -120))
    now = _event("evt-now", "Apple shares slide on demand worries", 0)
    rag.upsert_event(now)  # RagService.retrieve upserts before it queries

    hits = rag.query(now, top_k=5)

    assert [h.document_id for h in hits] == ["evt-old-1"]
