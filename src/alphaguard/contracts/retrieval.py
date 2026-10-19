"""RetrievalHit contract (ARCHITECTURE §7.3 / AG3)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

HitSource = Literal["qdrant", "fixture"]


class RetrievalHit(BaseModel):
    """Context item Agent 1 may see — must satisfy available_at <= event.published_at."""

    document_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    available_at: datetime
    source: HitSource
    score: float = 0.0

    @field_validator("available_at")
    @classmethod
    def available_at_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("available_at must be timezone-aware UTC")
        return value
