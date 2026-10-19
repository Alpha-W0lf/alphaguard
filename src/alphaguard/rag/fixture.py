"""Fixture RAG mode — curated RetrievalHit sidecars (no Qdrant)."""

from __future__ import annotations

import json
from pathlib import Path

from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.retrieval import RetrievalHit
from alphaguard.rag.asof import filter_hits_as_of


def load_fixture_hits(
    event: NewsEvent,
    sidecar_path: Path,
    top_k: int = 5,
) -> list[RetrievalHit]:
    if not sidecar_path.exists():
        raise FileNotFoundError(f"retrieval sidecar missing: {sidecar_path}")
    raw = json.loads(sidecar_path.read_text(encoding="utf-8"))
    rows = raw.get(event.event_id, [])
    hits = [RetrievalHit.model_validate(row) for row in rows]
    filtered = filter_hits_as_of(hits, event.published_at)
    filtered.sort(key=lambda h: h.score, reverse=True)
    return filtered[:top_k]
