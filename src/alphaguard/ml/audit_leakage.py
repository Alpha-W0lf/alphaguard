"""WP-C3: duplicates, as-of timestamps, horizon overlap, and the row embargo.

Construction duplicate: same ticker, America/New_York calendar date, and
normalized headline. That is the builder's dedup key. Extra headlines that
share a ``(ticker, feature_as_of)`` are dependence, not that defect.

As-of violation: stored ``feature_as_of`` is not the last completed session
at or before ``published_at``, that session's close is after ``published_at``,
or ``news_available_at`` (when present) is after ``published_at``. FinBERT has
no clock of its own; the headline is available at ``published_at``.

The recorded Phase B embargo is 5 global rows. On a multi-ticker frame that
can be shorter than five trading sessions, so a train label can reach the
next block. The trading-day purge is the fix; this module counts both.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from alphaguard.ml.audit_common import LABEL_HORIZON_SESSIONS
from alphaguard.ml.dataset_asof import (
    _xnys_calendar,
    feature_as_of_session,
    frame_session_indices,
)
from alphaguard.ml.dataset_ingest import normalize_headline
from alphaguard.ml.study_walkforward import (
    FoldIndex,
    apply_trading_day_embargo,
    horizon_overlap_count,
    prefix_end_before_session,
)


def construction_duplicate_count(df: pd.DataFrame) -> int:
    if "headline" not in df.columns or "ticker" not in df.columns:
        return 0
    published = pd.to_datetime(df["published_at"], utc=True)
    day = published.dt.tz_convert("America/New_York").dt.date.astype(str)
    key = (
        df["ticker"].astype(str)
        + "|"
        + day
        + "|"
        + df["headline"].map(normalize_headline)
    )
    return int(key.duplicated().sum())


def asof_repetition_count(df: pd.DataFrame) -> int:
    """Rows that share ``(ticker, feature_as_of)`` with another row."""
    if "ticker" not in df.columns or "feature_as_of" not in df.columns:
        return 0
    return int(df.duplicated(["ticker", "feature_as_of"], keep=False).sum())


def _as_utc(value: Any) -> datetime:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    return stamp.tz_convert("UTC").to_pydatetime()


def asof_violations(df: pd.DataFrame, calendar: Any | None = None) -> list[dict[str, Any]]:
    """Rows whose feature or news clock is after the decision cutoff."""
    cal = calendar or _xnys_calendar()
    schedule_close = cal.schedule["close"]
    close_by_day = {
        pd.Timestamp(ts).date(): schedule_close.loc[ts] for ts in schedule_close.index
    }
    violations: list[dict[str, Any]] = []
    news = df["news_available_at"] if "news_available_at" in df.columns else None
    for i, row in enumerate(df.itertuples(index=False)):
        published = _as_utc(row.published_at)
        reasons: list[str] = []
        if news is not None and not pd.isna(news.iloc[i]):
            if _as_utc(news.iloc[i]) > published:
                reasons.append("news_available_after_published")
        stored = getattr(row, "feature_as_of", None)
        if stored is None or (isinstance(stored, float) and np.isnan(stored)):
            reasons.append("feature_as_of_missing")
        else:
            feature_day = stored if isinstance(stored, date) else pd.Timestamp(stored).date()
            expected = feature_as_of_session(published, cal)
            if feature_day != expected:
                reasons.append("feature_as_of_mismatch")
            close = close_by_day.get(feature_day)
            if close is None or close > published:
                reasons.append("feature_close_after_published")
        if reasons:
            violations.append({"row": i, "reasons": reasons})
    return violations


def _unique_sessions(feature_idx: np.ndarray, start: int, end: int) -> int:
    gap = feature_idx[start:end]
    if len(gap) == 0:
        return 0
    return int(len(np.unique(gap)))


def _boundary_row(
    name: str,
    *,
    feature_idx: np.ndarray,
    label_end_idx: np.ndarray,
    train_end: int,
    next_start: int,
    next_end: int,
) -> dict[str, Any]:
    unique = _unique_sessions(feature_idx, train_end, next_start)
    overlaps = horizon_overlap_count(
        label_end_idx, feature_idx, train_end, next_start, next_end
    )
    return {
        "name": name,
        "train_end": int(train_end),
        "next_start": int(next_start),
        "next_end": int(next_end),
        "gap_rows": int(next_start - train_end),
        "unique_feature_sessions_in_gap": unique,
        "gap_shorter_than_horizon": unique < LABEL_HORIZON_SESSIONS,
        "overlap_rows": overlaps,
    }


def recorded_boundaries(
    folds: list[FoldIndex],
    n_rows: int,
    n_dev: int,
    feature_idx: np.ndarray,
    label_end_idx: np.ndarray,
) -> list[dict[str, Any]]:
    rows = [
        _boundary_row(
            f"fold_{fold.fold}",
            feature_idx=feature_idx,
            label_end_idx=label_end_idx,
            train_end=fold.train_end,
            next_start=fold.val_start,
            next_end=fold.val_end,
        )
        for fold in folds
    ]
    rows.append(
        _boundary_row(
            "locked_test",
            feature_idx=feature_idx,
            label_end_idx=label_end_idx,
            train_end=n_dev,
            next_start=n_dev,
            next_end=n_rows,
        )
    )
    return rows


def purged_boundaries(
    folds: list[FoldIndex],
    n_rows: int,
    n_dev: int,
    feature_idx: np.ndarray,
    label_end_idx: np.ndarray,
) -> list[dict[str, Any]]:
    """Same blocks after the trading-day purge. Overlap should be zero."""
    purged, _changed = apply_trading_day_embargo(folds, label_end_idx, feature_idx)
    rows = [
        _boundary_row(
            f"fold_{fold.fold}",
            feature_idx=feature_idx,
            label_end_idx=label_end_idx,
            train_end=fold.train_end,
            next_start=fold.val_start,
            next_end=fold.val_end,
        )
        for fold in purged
    ]
    train_end = prefix_end_before_session(
        label_end_idx,
        candidate_end=n_dev,
        next_session=int(np.min(feature_idx[n_dev:n_rows])),
    )
    rows.append(
        _boundary_row(
            "locked_test",
            feature_idx=feature_idx,
            label_end_idx=label_end_idx,
            train_end=train_end,
            next_start=n_dev,
            next_end=n_rows,
        )
    )
    return rows


def audit_leakage(
    df: pd.DataFrame,
    folds: list[FoldIndex],
    n_dev: int,
    *,
    feature_idx: np.ndarray | None = None,
    label_end_idx: np.ndarray | None = None,
) -> dict[str, Any]:
    if feature_idx is None or label_end_idx is None:
        feature_idx, label_end_idx = frame_session_indices(df)
    recorded = recorded_boundaries(folds, len(df), n_dev, feature_idx, label_end_idx)
    purged = purged_boundaries(folds, len(df), n_dev, feature_idx, label_end_idx)
    violations = asof_violations(df)
    overlap_rows = int(sum(row["overlap_rows"] for row in recorded))
    short = int(sum(1 for row in recorded if row["gap_shorter_than_horizon"]))
    purged_overlap = int(sum(row["overlap_rows"] for row in purged))
    return {
        "construction_duplicates": construction_duplicate_count(df),
        "asof_repetition_rows": asof_repetition_count(df),
        "asof_violation_count": len(violations),
        "asof_violations": violations,
        "finbert_clock": "headline at published_at; no separate FinBERT timestamp",
        "recorded_boundaries": recorded,
        "purged_boundaries": purged,
        "row_embargo_overlap_rows": overlap_rows,
        "row_embargo_short_boundaries": short,
        "purged_overlap_rows": purged_overlap,
    }
