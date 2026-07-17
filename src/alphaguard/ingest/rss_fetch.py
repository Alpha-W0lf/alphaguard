"""Fetch Yahoo Finance RSS feeds with retries (Guide 06)."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

import httpx

from alphaguard.ingest.rss_normalize import require_universe_ticker

logger = logging.getLogger(__name__)

FEED_URL_TEMPLATE = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&lang=en-US"
)
USER_AGENT = "AlphaGuard/0.1 (+https://github.com/Alpha-W0lf/alphaguard; research)"
DEFAULT_TIMEOUT_S = 10.0
MAX_ATTEMPTS = 3
BACKOFF_BASE_S = 0.5
BACKOFF_CAP_S = 8.0


class RssFetchError(RuntimeError):
    """Raised when a feed cannot be fetched after retries."""


def feed_url(ticker: str) -> str:
    ticker = require_universe_ticker(ticker)
    return FEED_URL_TEMPLATE.format(TICKER=ticker)


def _backoff_seconds(attempt: int) -> float:
    # attempt is 1-based after a failure; exponential + jitter
    delay = min(BACKOFF_CAP_S, BACKOFF_BASE_S * (2 ** (attempt - 1)))
    jitter = random.uniform(0, delay * 0.25)
    return delay + jitter


def fetch_feed(
    ticker: str,
    *,
    client: httpx.Client | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> bytes:
    """GET Yahoo RSS for ticker. Retries transport/timeout/429/5xx up to MAX_ATTEMPTS."""
    ticker = require_universe_ticker(ticker)
    url = feed_url(ticker)
    headers = {"User-Agent": USER_AGENT}
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout_s)
    last_error: Exception | None = None
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = http.get(url, headers=headers)
                if response.status_code in {429} or response.status_code >= 500:
                    raise RssFetchError(
                        f"HTTP {response.status_code} for {ticker} attempt={attempt}"
                    )
                if response.status_code >= 400:
                    raise RssFetchError(
                        f"HTTP {response.status_code} for {ticker} (non-retriable)"
                    )
                return response.content
            except RssFetchError as exc:
                last_error = exc
                if "non-retriable" in str(exc):
                    raise
                logger.warning("rss_fetch_retry ticker=%s attempt=%s error=%s", ticker, attempt, exc)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                logger.warning(
                    "rss_fetch_retry ticker=%s attempt=%s error=%s",
                    ticker,
                    attempt,
                    exc,
                )
            if attempt < MAX_ATTEMPTS:
                sleep_fn(_backoff_seconds(attempt))
        raise RssFetchError(
            f"exhausted {MAX_ATTEMPTS} attempts for {ticker}: {last_error}"
        ) from last_error
    finally:
        if owns_client:
            http.close()
