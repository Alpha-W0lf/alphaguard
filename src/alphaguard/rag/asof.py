"""As-of filtering for RetrievalHit (AG3)."""

from __future__ import annotations

from datetime import datetime

from alphaguard.contracts.retrieval import RetrievalHit


def filter_hits_as_of(
    hits: list[RetrievalHit],
    published_at: datetime,
) -> list[RetrievalHit]:
    """Drop any hit where available_at > event.published_at."""
    return [h for h in hits if h.available_at <= published_at]
