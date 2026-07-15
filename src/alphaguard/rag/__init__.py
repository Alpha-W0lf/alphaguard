"""RAG façade used exclusively by PipelineService."""

from __future__ import annotations

from pathlib import Path

from alphaguard.config import Settings
from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.retrieval import RetrievalHit
from alphaguard.rag.fixture import load_fixture_hits
from alphaguard.rag.service import QdrantRag


class RagService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._qdrant: QdrantRag | None = None

    def _qdrant_client(self) -> QdrantRag:
        if self._qdrant is None:
            self._qdrant = QdrantRag(
                url=self.settings.qdrant_url,
                collection=self.settings.qdrant_collection,
            )
        return self._qdrant

    def upsert_event(self, event: NewsEvent) -> None:
        """Durable Qdrant upsert only — used by Kafka ingest (no retrieve)."""
        if self.settings.alphaguard_rag_mode == "fixture":
            raise RuntimeError(
                "upsert_event requires ALPHAGUARD_RAG_MODE=qdrant; "
                "fixture mode has no vector store."
            )
        self._qdrant_client().upsert_event(event)

    def retrieve(self, event: NewsEvent) -> list[RetrievalHit]:
        if self.settings.alphaguard_rag_mode == "fixture":
            sidecar = self.settings.fixtures_dir / "retrieval_hits.json"
            return load_fixture_hits(event, sidecar, top_k=self.settings.top_k)

        qdrant = self._qdrant_client()
        qdrant.upsert_event(event)
        return qdrant.query(event, top_k=self.settings.top_k)


def default_sidecar_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "retrieval_hits.json"
