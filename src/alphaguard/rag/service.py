"""Qdrant RAG mode — embed + upsert/query with mandatory as-of filter."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.retrieval import RetrievalHit
from alphaguard.rag.asof import filter_hits_as_of

logger = logging.getLogger(__name__)

_EMBEDDER: Any | None = None


def _get_embedder() -> Any:
    global _EMBEDDER
    if _EMBEDDER is None:
        from sentence_transformers import SentenceTransformer

        _EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _EMBEDDER


def _embed(texts: list[str]) -> list[list[float]]:
    model = _get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


class QdrantRag:
    """Simple top-k vector retrieval with as-of filter. No reranker."""

    def __init__(self, url: str, collection: str) -> None:
        self.url = url
        self.collection = collection
        self._client: Any | None = None

    def _connect(self) -> Any:
        if self._client is None:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qm

            try:
                client = QdrantClient(url=self.url, timeout=3.0)
                client.get_collections()
            except Exception as exc:  # noqa: BLE001 — surface actionable mode hint
                raise RuntimeError(
                    f"Qdrant unreachable at {self.url}: {exc}. "
                    "Set ALPHAGUARD_RAG_MODE=fixture for smoke without Qdrant."
                ) from exc
            if not client.collection_exists(self.collection):
                client.create_collection(
                    collection_name=self.collection,
                    vectors_config=qm.VectorParams(size=384, distance=qm.Distance.COSINE),
                )
            self._client = client
        return self._client

    def upsert_event(self, event: NewsEvent) -> None:
        from qdrant_client.http import models as qm

        client = self._connect()
        vector = _embed([event.headline])[0]
        point = qm.PointStruct(
            id=abs(hash(event.event_id)) % (2**63 - 1),
            vector=vector,
            payload={
                "document_id": event.event_id,
                "text": event.headline,
                "ticker": event.ticker,
                "available_at": event.published_at.astimezone(timezone.utc).isoformat(),
                "source": "qdrant",
            },
        )
        client.upsert(collection_name=self.collection, points=[point], wait=True)

    def query(self, event: NewsEvent, top_k: int = 5) -> list[RetrievalHit]:
        from qdrant_client.http import models as qm

        client = self._connect()
        vector = _embed([event.headline])[0]
        # Over-fetch then filter as-of in application code (payload filter is belt).
        results = client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=max(top_k * 3, top_k),
            query_filter=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="ticker",
                        match=qm.MatchValue(value=event.ticker),
                    )
                ]
            ),
        )
        hits: list[RetrievalHit] = []
        for point in results:
            payload = point.payload or {}
            available_raw = payload.get("available_at")
            if available_raw is None:
                continue
            available_at = datetime.fromisoformat(str(available_raw).replace("Z", "+00:00"))
            hits.append(
                RetrievalHit(
                    document_id=str(payload.get("document_id", point.id)),
                    text=str(payload.get("text", "")),
                    ticker=str(payload.get("ticker", event.ticker)),
                    available_at=available_at,
                    source="qdrant",
                    score=float(point.score or 0.0),
                )
            )
        filtered = filter_hits_as_of(hits, event.published_at)
        return filtered[:top_k]
