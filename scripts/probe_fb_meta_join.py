#!/usr/bin/env python3
"""Join probe: FB headline calendar days ∩ META adjusted closes (no Yahoo FB)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.dataset_asof import default_yfinance_closes  # noqa: E402
from alphaguard.ml.dataset_ingest import discover_news_csv  # noqa: E402


def main() -> int:
    raw_dir = Path("data/raw/kaggle_stock_news")
    csv_path = discover_news_csv(raw_dir)
    df = pd.read_csv(csv_path)
    cols = {c.lower().strip(): c for c in df.columns}
    stock_col = cols.get("stock")
    date_col = cols.get("date")
    if not stock_col or not date_col:
        print("ERROR: CSV missing stock/date", file=sys.stderr)
        return 1
    fb = df.loc[df[stock_col].astype(str).str.strip().str.upper() == "FB"].copy()
    if fb.empty:
        print("fb_days=0 meta_same_day_closes=0 coverage=n/a")
        return 0
    # Archive mixes naive and tz-aware strings — normalize via UTC calendar date.
    fb["cal"] = pd.to_datetime(fb[date_col], errors="coerce", utc=True).dt.tz_convert(
        "America/New_York"
    ).dt.date
    fb = fb.dropna(subset=["cal"])
    days = sorted(set(fb["cal"].tolist()))
    start, end = days[0], days[-1]
    # Intentionally META only — default_yfinance_closes rejects FB.
    closes = default_yfinance_closes("META", start, end)
    close_days = set(closes.index.tolist()) if not closes.empty else set()
    hit = sum(1 for d in days if d in close_days)
    n = len(days)
    cov = f"{hit / n:.4f}" if n else "n/a"
    print(f"fb_days={n} meta_same_day_closes={hit} coverage={cov}")
    print(f"csv={csv_path} price_ticker=META (never FB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
