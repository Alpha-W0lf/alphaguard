"""Ingest helpers for Option B training news (Kaggle CSV → filtered rows)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd

from alphaguard.contracts.events import TICKER_UNIVERSE

SOURCE_DATASET_ID = "miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests"
BUILDER_VERSION = "0.1.1"
_WS = re.compile(r"\s+")
ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class ArchiveAliasRule:
    """Documented archive→universe rename (training ingest only)."""

    rule_id: str
    archive_symbol: str
    universe_ticker: str


# Extensible registry — add rows; do not silent-remap outside this table.
ARCHIVE_ALIAS_REGISTRY: tuple[ArchiveAliasRule, ...] = (
    ArchiveAliasRule("fb_meta_v1", "FB", "META"),
    ArchiveAliasRule("goog_googl_v1", "GOOG", "GOOGL"),
)
ARCHIVE_ALIAS_BY_SOURCE: dict[str, ArchiveAliasRule] = {
    r.archive_symbol: r for r in ARCHIVE_ALIAS_REGISTRY
}
# Yahoo must never be called with these archive sources on the builder path.
FORBIDDEN_PRICE_FETCH_TICKERS: frozenset[str] = frozenset(
    r.archive_symbol for r in ARCHIVE_ALIAS_REGISTRY
)
ALIAS_RULE_VERSION_ON = "+".join(r.rule_id for r in ARCHIVE_ALIAS_REGISTRY)


@dataclass(frozen=True)
class IngestStats:
    rows_raw: int
    rows_universe: int
    rows_after_dedup: int
    rows_sampled: int
    oou_dropped: int
    missing_fields_dropped: int
    universe_tickers_absent: tuple[str, ...]
    alias_candidates_oou: dict[str, int]
    alias_rule_version: str
    alias_applied_counts: dict[str, int]


def normalize_headline(text: str) -> str:
    return _WS.sub(" ", text.strip().lower())


def discover_news_csv(raw_dir: Path) -> Path:
    """Find the news CSV under a Kaggle unzip tree (document name in TRAINING_DATA.md)."""
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"raw cache missing: {raw_dir}")
    candidates = sorted(raw_dir.rglob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"no CSV under {raw_dir}")
    # Prefer minute-precision processed ratings (Kaggle data card).
    for p in candidates:
        if p.name.lower() == "analyst_ratings_processed.csv":
            return p
    preferred = [
        p
        for p in candidates
        if "processed" in p.name.lower()
        and any(tok in p.name.lower() for tok in ("analyst", "news", "headline", "benzinga"))
    ]
    pool = preferred or [
        p
        for p in candidates
        if any(tok in p.name.lower() for tok in ("analyst", "news", "headline", "benzinga"))
    ] or candidates
    return max(pool, key=lambda p: p.stat().st_size)


def _require_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower = {c.lower().strip(): c for c in df.columns}
    # title is the processed-file alias for headline (Kaggle data card).
    if "headline" not in lower and "title" in lower:
        lower["headline"] = lower["title"]
    if "headline" not in lower and "article title" in lower:
        lower["headline"] = lower["article title"]
    need = {"date": None, "stock": None, "headline": None}
    for logical in need:
        if logical not in lower:
            raise ValueError(
                f"CSV missing required column {logical!r}; got {list(df.columns)}"
            )
        need[logical] = lower[logical]
    out = df.rename(
        columns={
            need["date"]: "date",
            need["stock"]: "stock",
            need["headline"]: "headline",
        }
    )
    return out[["date", "stock", "headline"]].copy()


def parse_published_timestamp(value: Any) -> datetime | None:
    """Parse source timestamp when a clock is present.

    Kaggle processed file documents Eastern wall time (UTC-4). Naive datetimes are
    interpreted as America/New_York, then converted to UTC.
    Date-only values return None so the caller can apply the 09:30 ET soft pin.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    raw = str(value).strip()
    has_clock = bool(re.search(r"\d{1,2}:\d{2}", raw))
    if not has_clock and ts.hour == 0 and ts.minute == 0 and ts.second == 0:
        return None
    if ts.tzinfo is None:
        local = datetime(
            ts.year, ts.month, ts.day, ts.hour, ts.minute, int(ts.second), tzinfo=ET
        )
        return local.astimezone(timezone.utc)
    return ts.to_pydatetime().astimezone(timezone.utc)


def parse_calendar_date(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def source_row_hash(date_s: str, stock: str, headline: str) -> str:
    payload = f"{date_s}|{stock}|{headline}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def event_id_for(ticker: str, calendar_date: date, normalized_headline: str) -> str:
    import uuid

    digest = hashlib.sha256(normalized_headline.encode("utf-8")).hexdigest()[:16]
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"alphaguard:train:{ticker}:{calendar_date.isoformat()}:{digest}",
        )
    )


def _apply_archive_aliases(
    tickers: pd.Series, *, apply_archive_aliases: bool
) -> tuple[pd.Series, dict[str, int], dict[str, int], str]:
    """Map registry sources → universe tickers; provenance + honesty candidates."""
    applied: dict[str, int] = {}
    candidates: dict[str, int] = {}
    out = tickers.copy()
    for rule in ARCHIVE_ALIAS_REGISTRY:
        mask = tickers == rule.archive_symbol
        n = int(mask.sum())
        if n == 0:
            continue
        key = f"{rule.archive_symbol}→{rule.universe_ticker}"
        if apply_archive_aliases:
            out = out.where(~mask, rule.universe_ticker)
            applied[key] = n
        else:
            candidates[rule.archive_symbol] = n
    version = ALIAS_RULE_VERSION_ON if apply_archive_aliases else "off"
    return out, applied, candidates, version


def load_filter_dedup_sample(
    csv_path: Path,
    *,
    target_rows: int = 500,
    random_seed: int = 42,
    apply_archive_aliases: bool = True,
) -> tuple[pd.DataFrame, IngestStats]:
    raw = pd.read_csv(csv_path)
    rows_raw = len(raw)
    df = _require_columns(raw)
    missing = df["date"].isna() | df["stock"].isna() | df["headline"].isna()
    missing |= df["headline"].astype(str).str.strip().eq("")
    missing_fields_dropped = int(missing.sum())
    df = df.loc[~missing].copy()

    df["ticker"] = df["stock"].astype(str).str.strip().str.upper()
    df["ticker"], alias_applied_counts, alias_candidates_oou, alias_rule_version = (
        _apply_archive_aliases(df["ticker"], apply_archive_aliases=apply_archive_aliases)
    )
    in_u = df["ticker"].isin(TICKER_UNIVERSE)
    oou_dropped = int((~in_u).sum())
    df = df.loc[in_u].copy()
    rows_universe = len(df)
    universe_tickers_absent = tuple(
        sorted(t for t in TICKER_UNIVERSE if int((df["ticker"] == t).sum()) == 0)
    )

    df["calendar_date"] = df["date"].map(parse_calendar_date)
    bad_date = df["calendar_date"].isna()
    missing_fields_dropped += int(bad_date.sum())
    df = df.loc[~bad_date].copy()

    df["headline"] = df["headline"].astype(str)
    df["normalized_headline"] = df["headline"].map(normalize_headline)
    df = df.drop_duplicates(
        subset=["ticker", "calendar_date", "normalized_headline"], keep="first"
    )
    rows_after_dedup = len(df)

    if rows_after_dedup == 0:
        raise ValueError("no rows remain after universe filter + dedup")

    # Stratified sample across tickers when possible.
    if rows_after_dedup <= target_rows:
        sampled = df.copy()
    else:
        per = max(1, target_rows // len(TICKER_UNIVERSE))
        parts: list[pd.DataFrame] = []
        taken_idx: set[Any] = set()
        for ticker in sorted(TICKER_UNIVERSE):
            sub = df.loc[df["ticker"] == ticker]
            if sub.empty:
                continue
            n = min(len(sub), per)
            part = sub.sample(n=n, random_state=random_seed)
            parts.append(part)
            taken_idx.update(part.index.tolist())
        sampled = pd.concat(parts, axis=0) if parts else df.head(0)
        if len(sampled) < target_rows:
            remain = df.loc[~df.index.isin(taken_idx)]
            need = target_rows - len(sampled)
            if need > 0 and len(remain) > 0:
                extra = remain.sample(n=min(need, len(remain)), random_state=random_seed)
                sampled = pd.concat([sampled, extra], axis=0)
        if len(sampled) > target_rows:
            sampled = sampled.sample(n=target_rows, random_state=random_seed)

    sampled = sampled.reset_index(drop=True)
    sampled["source_dataset_id"] = SOURCE_DATASET_ID
    sampled["source_row_hash"] = [
        source_row_hash(str(r.date), str(r.stock), str(r.headline))
        for r in sampled.itertuples(index=False)
    ]
    sampled["event_id"] = [
        event_id_for(str(r.ticker), r.calendar_date, str(r.normalized_headline))
        for r in sampled.itertuples(index=False)
    ]
    if bool(sampled["event_id"].duplicated().any()):
        raise RuntimeError(
            "duplicate event_id after sample — stratified sampling bug or colliding headlines"
        )
    sampled["builder_version"] = BUILDER_VERSION
    sampled["published_at_parsed"] = [
        parse_published_timestamp(r.date) for r in sampled.itertuples(index=False)
    ]

    stats = IngestStats(
        rows_raw=rows_raw,
        rows_universe=rows_universe,
        rows_after_dedup=rows_after_dedup,
        rows_sampled=len(sampled),
        oou_dropped=oou_dropped,
        missing_fields_dropped=missing_fields_dropped,
        universe_tickers_absent=universe_tickers_absent,
        alias_candidates_oou=alias_candidates_oou,
        alias_rule_version=alias_rule_version,
        alias_applied_counts=alias_applied_counts,
    )
    return sampled, stats


def reject_oou_tickers(tickers: Iterable[str]) -> list[str]:
    """Return OOU tickers (for unit tests / CLI reporting)."""
    return [t for t in tickers if t not in TICKER_UNIVERSE]
