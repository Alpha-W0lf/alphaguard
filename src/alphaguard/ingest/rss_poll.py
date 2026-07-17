"""RSS poll orchestration — fetch → normalize → produce (Guide 06)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from kafka import KafkaProducer

from alphaguard.contracts.events import TICKER_UNIVERSE, OutOfUniverseTickerError
from alphaguard.ingest.producer import KafkaProduceError, produce_event
from alphaguard.ingest.rss_fetch import RssFetchError, fetch_feed
from alphaguard.ingest.rss_normalize import (
    RssParseError,
    NormalizeResult,
    normalize_rss_xml,
    require_universe_ticker,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 10
DEFAULT_INTERVAL_SEC = 120


@dataclass
class PollSummary:
    tickers: list[str] = field(default_factory=list)
    fetched: int = 0
    produced: int = 0
    skipped_items: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tickers": self.tickers,
            "fetched": self.fetched,
            "produced": self.produced,
            "skipped_items": self.skipped_items,
            "errors": self.errors,
        }


def resolve_tickers(ticker_arg: str) -> list[str]:
    """Parse CLI --ticker (symbol or 'all'). Raises OutOfUniverseTickerError / ValueError."""
    raw = ticker_arg.strip()
    if not raw:
        raise ValueError("ticker must be non-empty")
    if raw.lower() == "all":
        return sorted(TICKER_UNIVERSE)
    return [require_universe_ticker(raw)]


def poll_once(
    tickers: Sequence[str],
    producer: KafkaProducer,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    fetch_fn: Callable[[str], bytes] = fetch_feed,
    normalize_fn: Callable[[bytes, str], NormalizeResult] = normalize_rss_xml,
) -> PollSummary:
    """Fetch/normalize/produce for each ticker. Continues on hard failures; records errors."""
    summary = PollSummary(tickers=list(tickers))
    for ticker in tickers:
        try:
            raw = fetch_fn(ticker)
            summary.fetched += 1
            result = normalize_fn(raw, ticker)
            summary.skipped_items += result.skipped_items
            events = result.events[:max_items]
            if not events:
                logger.info("rss_empty ticker=%s skipped_items=%s", ticker, result.skipped_items)
                continue
            for event in events:
                produce_event(producer, event)
                summary.produced += 1
        except (RssFetchError, RssParseError, KafkaProduceError, OutOfUniverseTickerError) as exc:
            msg = f"{ticker}: {exc}"
            summary.errors.append(msg)
            logger.error("rss_poll_ticker_failed %s", msg)
        except Exception as exc:  # noqa: BLE001 — keep other tickers running
            msg = f"{ticker}: {exc}"
            summary.errors.append(msg)
            logger.error("rss_poll_ticker_failed %s", msg)
    return summary


def exit_code_for_summary(summary: PollSummary, *, usage_error: bool = False) -> int:
    if usage_error:
        return 2
    if summary.errors:
        return 1
    return 0


def poll_loop(
    tickers: Sequence[str],
    producer: KafkaProducer,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    interval_sec: int = DEFAULT_INTERVAL_SEC,
    fetch_fn: Callable[[str], bytes] = fetch_feed,
    normalize_fn: Callable[[bytes, str], NormalizeResult] = normalize_rss_xml,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    """Demo loop until KeyboardInterrupt. Not a production daemon."""
    logger.info(
        "rss_loop_start tickers=%s max_items=%s interval_sec=%s",
        list(tickers),
        max_items,
        interval_sec,
    )
    try:
        while True:
            summary = poll_once(
                tickers,
                producer,
                max_items=max_items,
                fetch_fn=fetch_fn,
                normalize_fn=normalize_fn,
            )
            logger.info("rss_loop_iteration %s", summary.to_dict())
            sleep_fn(float(interval_sec))
    except KeyboardInterrupt:
        logger.info("rss_loop_stopped")
