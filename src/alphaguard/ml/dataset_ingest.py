"""Ingest helpers for Option B training news (Kaggle CSV → filtered rows)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from alphaguard.contracts.events import TICKER_UNIVERSE

SOURCE_DATASET_ID = "miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests"
BUILDER_VERSION = "0.1.0"
_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class IngestStats:
    rows_raw: int
    rows_universe: int
    rows_after_dedup: int
    rows_sampled: int
    oou_dropped: int
    missing_fields_dropped: int


def normalize_headline(text: str) -> str:
    return _WS.sub(" ", text.strip().lower())


def discover_news_csv(raw_dir: Path) -> Path:
    """Find the news CSV under a Kaggle unzip tree (document name in TRAINING_DATA.md)."""
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"raw cache missing: {raw_dir}")
    candidates = sorted(raw_dir.rglob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"no CSV under {raw_dir}")
    preferred = [
        p
        for p in candidates
        if any(tok in p.name.lower() for tok in ("analyst", "news", "headline", "benzinga"))
    ]
    pool = preferred or candidates
    # Prefer largest file when multiple match (full dump vs sample).
    return max(pool, key=lambda p: p.stat().st_size)


def _require_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower = {c.lower(): c for c in df.columns}
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


def load_filter_dedup_sample(
    csv_path: Path,
    *,
    target_rows: int = 500,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, IngestStats]:
    raw = pd.read_csv(csv_path)
    rows_raw = len(raw)
    df = _require_columns(raw)
    missing = df["date"].isna() | df["stock"].isna() | df["headline"].isna()
    missing |= df["headline"].astype(str).str.strip().eq("")
    missing_fields_dropped = int(missing.sum())
    df = df.loc[~missing].copy()

    df["ticker"] = df["stock"].astype(str).str.strip().str.upper()
    in_u = df["ticker"].isin(TICKER_UNIVERSE)
    oou_dropped = int((~in_u).sum())
    df = df.loc[in_u].copy()
    rows_universe = len(df)

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
        sampled = df
    else:
        per = max(1, target_rows // len(TICKER_UNIVERSE))
        parts: list[pd.DataFrame] = []
        for ticker in sorted(TICKER_UNIVERSE):
            sub = df.loc[df["ticker"] == ticker]
            if sub.empty:
                continue
            n = min(len(sub), per)
            parts.append(sub.sample(n=n, random_state=random_seed))
        sampled = pd.concat(parts, ignore_index=True) if parts else df.head(0)
        if len(sampled) < target_rows:
            remain = df.loc[~df.index.isin(sampled.index)]
            need = target_rows - len(sampled)
            if need > 0 and len(remain) > 0:
                extra = remain.sample(n=min(need, len(remain)), random_state=random_seed)
                sampled = pd.concat([sampled, extra], ignore_index=True)
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
    sampled["builder_version"] = BUILDER_VERSION

    stats = IngestStats(
        rows_raw=rows_raw,
        rows_universe=rows_universe,
        rows_after_dedup=rows_after_dedup,
        rows_sampled=len(sampled),
        oou_dropped=oou_dropped,
        missing_fields_dropped=missing_fields_dropped,
    )
    return sampled, stats


def reject_oou_tickers(tickers: Iterable[str]) -> list[str]:
    """Return OOU tickers (for unit tests / CLI reporting)."""
    return [t for t in tickers if t not in TICKER_UNIVERSE]
