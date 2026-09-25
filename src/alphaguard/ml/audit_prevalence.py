"""WP-C2: fold prevalence, regime versus artifact.

A fold is an artifact when positives are one ticker (>= 80 percent), one
ticker-day (>= 25 percent), a construction duplicate, or an interior gap of
more than 20 XNYS sessions. Otherwise it is a regime when positives are
spread across at least two tickers (each >= 10 percent) and the same-day
QQQ forward 5-day return is negative on at least half of those positives.
QQQ is the market ETF in this freeze. SPY has no rows. ``spy_return_5d`` is
the prior window and is not the alignment test.

Any other fold is an artifact because the audit has only these two labels.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from alphaguard.ml.audit_common import feature_dates, json_float, prevalence, slice_bounds
from alphaguard.ml.dataset_ingest import normalize_headline
from alphaguard.ml.study_walkforward import FoldIndex

ONE_TICKER_POSITIVE_SHARE = 0.80
ONE_DAY_POSITIVE_SHARE = 0.25
SPREAD_TICKER_SHARE = 0.10
SPREAD_MIN_TICKERS = 2
INGEST_GAP_SESSIONS = 20
MARKET_COVERAGE_MIN = 0.50
MARKET_TICKER = "QQQ"


def _share_table(counts: pd.Series, k: int) -> list[dict[str, Any]]:
    total = int(counts.sum())
    rows: list[dict[str, Any]] = []
    for key, n in counts.head(k).items():
        rows.append(
            {
                "key": str(key),
                "n": int(n),
                "share": json_float(n / total) if total else 0.0,
            }
        )
    return rows


def _max_gap(dates: list[Any], session_index: dict[Any, int] | None) -> int | None:
    if session_index is None or len(dates) < 2:
        return None
    ordered = sorted({day for day in dates if day in session_index})
    if len(ordered) < 2:
        return None
    gaps = [
        session_index[b] - session_index[a]
        for a, b in zip(ordered, ordered[1:], strict=False)
    ]
    return int(max(gaps)) if gaps else None


def _construction_positive_dups(pos: pd.DataFrame) -> int:
    if pos.empty or "headline" not in pos.columns:
        return 0
    published = pd.to_datetime(pos["published_at"], utc=True)
    day = published.dt.tz_convert("America/New_York").dt.date.astype(str)
    key = (
        pos["ticker"].astype(str)
        + "|"
        + day
        + "|"
        + pos["headline"].map(normalize_headline)
    )
    return int(key.duplicated().sum())


def classify_slice(
    part: pd.DataFrame,
    *,
    market_fwd_by_date: pd.Series,
    session_index: dict[Any, int] | None = None,
) -> dict[str, Any]:
    """Label one fold or the locked test as regime or artifact."""
    part = part.reset_index(drop=True)
    dates = feature_dates(part)
    y = part["label_high_risk"].to_numpy(dtype=int)
    pos_idx = np.flatnonzero(y == 1)
    pos = part.iloc[pos_idx].copy()
    pos_dates = dates.iloc[pos_idx]
    n_pos = int(len(pos))
    ticker_counts = pos.groupby("ticker").size().sort_values(ascending=False) if n_pos else pd.Series(dtype=int)
    day_key = pos["ticker"].astype(str) + "|" + pos_dates.astype(str) if n_pos else pd.Series(dtype=str)
    day_counts = day_key.value_counts() if n_pos else pd.Series(dtype=int)
    top_ticker_share = float(ticker_counts.iloc[0] / n_pos) if n_pos else 0.0
    top_day_share = float(day_counts.iloc[0] / n_pos) if n_pos else 0.0
    spread_tickers = int((ticker_counts / n_pos >= SPREAD_TICKER_SHARE).sum()) if n_pos else 0
    dup_pos = _construction_positive_dups(pos)
    gap = _max_gap(list(dates.unique()), session_index)
    market = pos_dates.map(market_fwd_by_date) if n_pos else pd.Series(dtype=float)
    known = market.notna() if n_pos else pd.Series(dtype=bool)
    coverage = float(known.mean()) if n_pos else 0.0
    market_median = float(market[known].median()) if known.any() else None
    reasons: list[str] = []
    if top_ticker_share >= ONE_TICKER_POSITIVE_SHARE:
        reasons.append("one_ticker")
    if top_day_share >= ONE_DAY_POSITIVE_SHARE:
        reasons.append("one_ticker_day")
    if dup_pos > 0:
        reasons.append("construction_duplicate")
    if gap is not None and gap > INGEST_GAP_SESSIONS:
        reasons.append("ingest_gap")
    spread = spread_tickers >= SPREAD_MIN_TICKERS
    aligned = (
        market_median is not None
        and market_median < 0.0
        and coverage >= MARKET_COVERAGE_MIN
    )
    if reasons:
        verdict = "artifact"
    elif spread and aligned:
        verdict = "regime"
        reasons.append("spread_and_market_drawdown")
    else:
        verdict = "artifact"
        reasons.append("not_a_market_drawdown")
    date_counts = pos_dates.astype(str).value_counts() if n_pos else pd.Series(dtype=int)
    return {
        "verdict": verdict,
        "reasons": reasons,
        "n": int(len(part)),
        "n_positive": n_pos,
        "prevalence": json_float(prevalence(y)),
        "ticker_count": int(part["ticker"].nunique()),
        "positive_ticker_count": int(pos["ticker"].nunique()) if n_pos else 0,
        "date_min": str(min(dates)) if len(dates) else None,
        "date_max": str(max(dates)) if len(dates) else None,
        "top_ticker_share": json_float(top_ticker_share),
        "top_day_share": json_float(top_day_share),
        "top5_tickers": _share_table(ticker_counts, 5),
        "top5_dates": _share_table(date_counts, 5),
        "top5_date_share": json_float(float(date_counts.head(5).sum() / n_pos)) if n_pos else 0.0,
        "top5_ticker_share": json_float(float(ticker_counts.head(5).sum() / n_pos)) if n_pos else 0.0,
        "construction_duplicate_positives": dup_pos,
        "max_interior_session_gap": gap,
        "market_ticker": MARKET_TICKER,
        "market_coverage": json_float(coverage),
        "market_fwd_median_on_positives": json_float(market_median),
    }


def market_fwd_by_date(df: pd.DataFrame) -> pd.Series:
    """Same-day median forward return of the market ETF (QQQ)."""
    dates = feature_dates(df)
    qqq = df.loc[df["ticker"].astype(str) == MARKET_TICKER, "fwd_return_5d"]
    if qqq.empty:
        return pd.Series(dtype=float)
    return qqq.groupby(dates.loc[qqq.index]).median()


def daily_fwd_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Cross-sectional median of ``fwd_return_5d`` by feature date."""
    dates = feature_dates(df)
    daily = df.groupby(dates)["fwd_return_5d"].median()
    if daily.empty:
        return {"n_dates": 0}
    return {
        "n_dates": int(len(daily)),
        "mean": json_float(daily.mean()),
        "std": json_float(daily.std(ddof=1)) if len(daily) > 1 else 0.0,
        "p10": json_float(daily.quantile(0.10)),
        "p50": json_float(daily.quantile(0.50)),
        "p90": json_float(daily.quantile(0.90)),
    }


def load_phaseb_fold_metrics(run_dir: Path) -> list[dict[str, Any]]:
    """Per-seed fold F1 and AUPRC lift from an existing Phase B run directory."""
    rows: list[dict[str, Any]] = []
    if not run_dir.is_dir():
        return rows
    for path in sorted(run_dir.glob("seed*/run.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        walk = payload.get("walk_forward") or {}
        for fold in walk.get("folds") or []:
            rate = float(fold["positive_rate"])
            auprc = float(fold["auprc"])
            rows.append(
                {
                    "seed": int(payload["seed"]),
                    "fold": int(fold["fold"]),
                    "f1": json_float(fold["f1"]),
                    "auprc": json_float(auprc),
                    "positive_rate": json_float(rate),
                    "auprc_lift": json_float(auprc / rate) if rate else None,
                    "n_rows": int(fold["n_rows"]),
                }
            )
    return rows


def audit_prevalence(
    df: pd.DataFrame,
    folds: list[FoldIndex],
    n_dev: int,
    *,
    session_index: dict[Any, int] | None = None,
    phaseb_metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    market = market_fwd_by_date(df)
    slices: list[dict[str, Any]] = []
    for bound in slice_bounds(folds, len(df), n_dev):
        part = df.iloc[bound["start"] : bound["end"]]
        row = classify_slice(part, market_fwd_by_date=market, session_index=session_index)
        row["name"] = bound["name"]
        row["fold"] = bound["fold"]
        slices.append(row)
    explicit = next((row for row in slices if row.get("fold") == 1), None)
    return {
        "market_fwd_distribution": daily_fwd_distribution(df),
        "spy_return_5d_note": "spy_return_5d is the prior 5-day feature, not the label window",
        "slices": slices,
        "explicit_fold_1_prevalence_0_2806": explicit,
        "phaseb_fold_metrics": phaseb_metrics or [],
        "auprc_lift_is_not_a_floor": True,
        "any_artifact": any(
            row["verdict"] == "artifact" for row in slices if row["name"] != "locked_test"
        ),
    }
