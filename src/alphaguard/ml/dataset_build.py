"""Option B dataset builder — Kaggle news → training_events.parquet (no XGBoost train)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from alphaguard.ml.dataset_asof import (
    compute_features_and_label,
    published_at_from_calendar_date,
)
from alphaguard.ml.dataset_finbert import score_headlines
from alphaguard.ml.dataset_ingest import (
    SOURCE_DATASET_ID,
    discover_news_csv,
    load_filter_dedup_sample,
)

REQUIRED_COLUMNS = [
    "event_id",
    "headline",
    "ticker",
    "published_at",
    "feature_as_of",
    "finbert_sentiment",
    "volatility_20d",
    "return_5d_prior",
    "return_20d_prior",
    "spy_return_5d",
    "fwd_return_5d",
    "label_high_risk",
    "source_dataset_id",
    "source_row_hash",
    "builder_version",
]

DEFAULT_RAW = Path("data/raw/kaggle_stock_news")
DEFAULT_OUT = Path("data/derived/training_events.parquet")
KAGGLE_SLUG = SOURCE_DATASET_ID


def ensure_kaggle_download(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    try:
        return discover_news_csv(raw_dir)
    except FileNotFoundError:
        pass
    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_SLUG,
        "-p",
        str(raw_dir),
        "--unzip",
    ]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "kaggle CLI not found. Install kaggle and place credentials in "
            "~/.kaggle/kaggle.json, or unzip the dataset under "
            f"{raw_dir} and re-run."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"kaggle download failed ({exc.returncode}). Check credentials/network, "
            f"or provide an offline unzip under {raw_dir}."
        ) from exc
    return discover_news_csv(raw_dir)


def build_training_events(
    *,
    raw_dir: Path = DEFAULT_RAW,
    out_path: Path = DEFAULT_OUT,
    target_rows: int = 500,
    random_seed: int = 42,
    allow_shortfall: bool = False,
    skip_download: bool = False,
    skip_finbert: bool = False,
    fetch_closes: Any | None = None,
) -> pd.DataFrame:
    if skip_download:
        csv_path = discover_news_csv(raw_dir)
    else:
        csv_path = ensure_kaggle_download(raw_dir)

    sampled, stats = load_filter_dedup_sample(
        csv_path, target_rows=target_rows, random_seed=random_seed
    )
    print(
        f"ingest: raw={stats.rows_raw} universe={stats.rows_universe} "
        f"dedup={stats.rows_after_dedup} sampled={stats.rows_sampled} "
        f"oou_dropped={stats.oou_dropped} missing_dropped={stats.missing_fields_dropped}"
    )
    print(f"csv_discovered={csv_path}")

    rows: list[dict[str, Any]] = []
    dropped_label = 0
    for r in sampled.itertuples(index=False):
        published_at = published_at_from_calendar_date(r.calendar_date)
        feats = compute_features_and_label(
            ticker=str(r.ticker),
            published_at=published_at,
            fetch_closes=fetch_closes,
        )
        if feats is None:
            dropped_label += 1
            continue
        rows.append(
            {
                "event_id": r.event_id,
                "headline": r.headline,
                "ticker": r.ticker,
                "published_at": published_at,
                "source_dataset_id": r.source_dataset_id,
                "source_row_hash": r.source_row_hash,
                "builder_version": r.builder_version,
                **feats,
            }
        )

    if not rows:
        raise RuntimeError("all sampled rows dropped during as-of/label join")

    df = pd.DataFrame(rows)
    if skip_finbert:
        df["finbert_sentiment"] = 0.0
        print("WARNING: skip_finbert=True — finbert_sentiment set to 0.0 (dev only)")
    else:
        print(
            "FinBERT batch: prefer Kafka/Qdrant/Ollama down (resource_mode=finbert_train)"
        )
        df["finbert_sentiment"] = score_headlines(df["headline"].tolist())

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"missing columns: {missing}")
    df = df[REQUIRED_COLUMNS]

    n = len(df)
    if n < target_rows and not allow_shortfall:
        raise RuntimeError(
            f"shortfall: got {n} rows after joins (target {target_rows}). "
            "Re-run with --allow-shortfall after documenting the shortfall."
        )
    if n < target_rows:
        print(f"SHORTFALL: {n} < {target_rows} (--allow-shortfall)")

    df = df.sort_values("published_at").reset_index(drop=True)
    split = int(n * 0.8)
    print(f"time_split preview: train={split} test={n - split} (no train performed)")
    print("rows_by_ticker:")
    print(df["ticker"].value_counts().sort_index().to_string())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"wrote {out_path} rows={n}")
    return df


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build Option B training_events.parquet")
    p.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--target-rows", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--allow-shortfall", action="store_true")
    p.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing CSV under raw-dir only",
    )
    p.add_argument(
        "--skip-finbert",
        action="store_true",
        help="Dev-only: zero sentiment (do not use for Option B claims)",
    )
    args = p.parse_args(argv)
    try:
        build_training_events(
            raw_dir=args.raw_dir,
            out_path=args.out,
            target_rows=args.target_rows,
            random_seed=args.seed,
            allow_shortfall=args.allow_shortfall,
            skip_download=args.skip_download,
            skip_finbert=args.skip_finbert,
        )
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
