"""News event contract + locked ticker universe (ARCHITECTURE §7.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

TICKER_UNIVERSE: frozenset[str] = frozenset(
    {"AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "SPY", "QQQ"}
)

SourceKind = Literal["fixture", "rss", "kaggle", "csv"]


class OutOfUniverseTickerError(ValueError):
    """Raised when a ticker is not in the locked v1 universe."""


class NewsEvent(BaseModel):
    """Ingress / fixture news event. Event clock = published_at (UTC)."""

    event_id: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    ticker: str
    source: SourceKind
    published_at: datetime
    url: str | None = None

    @field_validator("ticker")
    @classmethod
    def ticker_in_universe(cls, value: str) -> str:
        ticker = value.strip().upper()
        if ticker not in TICKER_UNIVERSE:
            raise OutOfUniverseTickerError(
                f"ticker {value!r} is out of universe; "
                f"allowed={sorted(TICKER_UNIVERSE)}"
            )
        return ticker

    @field_validator("headline")
    @classmethod
    def headline_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("headline must be non-empty")
        return value.strip()

    @field_validator("published_at")
    @classmethod
    def published_at_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("published_at must be timezone-aware UTC")
        return value
