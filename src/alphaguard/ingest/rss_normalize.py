"""Normalize Yahoo RSS XML bytes into NewsEvent rows (Guide 06)."""

from __future__ import annotations

import hashlib
import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import NamedTuple

from alphaguard.contracts.events import TICKER_UNIVERSE, NewsEvent, OutOfUniverseTickerError

logger = logging.getLogger(__name__)


class RssParseError(ValueError):
    """Raised when XML cannot be treated as an RSS channel/feed."""


class NormalizeResult(NamedTuple):
    events: list[NewsEvent]
    skipped_items: int


def require_universe_ticker(ticker: str) -> str:
    """Validate ticker ∈ locked universe; raise OutOfUniverseTickerError if not."""
    cleaned = ticker.strip().upper()
    if cleaned not in TICKER_UNIVERSE:
        raise OutOfUniverseTickerError(
            f"ticker {ticker!r} is out of universe; allowed={sorted(TICKER_UNIVERSE)}"
        )
    return cleaned


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _child_text(item: ET.Element, name: str) -> str | None:
    for child in item:
        if _local_tag(child.tag) == name:
            text = (child.text or "").strip()
            return text or None
    return None


def _parse_pub_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def stable_item_key(*, guid: str | None, link: str | None, title: str, published_at: datetime) -> str:
    if guid:
        return guid
    if link:
        return link
    digest = hashlib.sha256(f"{title}|{published_at.isoformat()}".encode()).hexdigest()[:32]
    return digest


def make_rss_event_id(ticker: str, item_key: str) -> str:
    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"alphaguard:rss:{ticker}:{item_key}")
    )


def normalize_rss_xml(raw: bytes, ticker: str) -> NormalizeResult:
    """Parse RSS XML → NewsEvents for ticker. Skips malformed items; fails closed on bad feed."""
    ticker = require_universe_ticker(ticker)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise RssParseError(f"invalid XML: {exc}") from exc

    channel = None
    if _local_tag(root.tag) == "rss":
        for child in root:
            if _local_tag(child.tag) == "channel":
                channel = child
                break
    elif _local_tag(root.tag) == "channel":
        channel = root
    if channel is None:
        raise RssParseError("RSS channel element not found")

    events: list[NewsEvent] = []
    skipped = 0
    for item in channel:
        if _local_tag(item.tag) != "item":
            continue
        title = _child_text(item, "title")
        link = _child_text(item, "link")
        guid = _child_text(item, "guid")
        published_at = _parse_pub_date(_child_text(item, "pubDate"))
        if not title or published_at is None:
            skipped += 1
            logger.warning(
                "rss_item_skipped ticker=%s reason=missing_title_or_date title=%r",
                ticker,
                title,
            )
            continue
        # Link optional for NewsEvent.url, but prefer it for stable key when no guid.
        item_key = stable_item_key(
            guid=guid, link=link, title=title, published_at=published_at
        )
        event_id = make_rss_event_id(ticker, item_key)
        events.append(
            NewsEvent(
                event_id=event_id,
                headline=title,
                ticker=ticker,
                source="rss",
                published_at=published_at,
                url=link,
            )
        )
    return NormalizeResult(events=events, skipped_items=skipped)
