"""Option B dataset builder — Kaggle news → training_events.parquet (no XGBoost train)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from alphaguard.contracts.events import TICKER_UNIVERSE
from alphaguard.ml.dataset_asof import (
    compute_features_and_label,
    make_cached_close_fetcher,
    published_at_from_calendar_date,
)
from alphaguard.ml.dataset_finbert import score_headlines
from alphaguard.ml.dataset_ingest import (
    SOURCE_DATASET_ID,
    discover_news_csv,
    load_filter_dedup_sample,
)


def _alias_fail_closed_message(stats: Any) -> str:
    applied = getattr(stats, "alias_applied_counts", {}) or {}
    version = getattr(stats, "alias_rule_version", "off")
    if applied:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(applied.items()))
        return (
            "all sampled rows dropped during as-of/label join "
            f"(documented aliases {version}: {detail}; "
            "target tickers META/GOOGL — never Yahoo FB/GOOG)"
        )
    return "all sampled rows dropped during as-of/label join"

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
    "rs_20d",
    "drawdown_20d",
    "volatility_5d",
    "spy_volatility_20d",
    "fwd_return_5d",
    "label_high_risk",
    "source_dataset_id",
    "source_row_hash",
    "builder_version",
]

# Served-universe flag is metadata for eval slices; not a model feature.
OUTPUT_COLUMNS = REQUIRED_COLUMNS + ["served_universe"]

DEFAULT_RAW = Path("data/raw/kaggle_stock_news")
DEFAULT_OUT = Path("data/derived/training_events.parquet")
KAGGLE_SLUG = SOURCE_DATASET_ID


def load_training_universe_file(path: Path) -> frozenset[str]:
    """Load tickers from candidate_tickers.json (list or ``candidate_tickers`` key)."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if "candidate_tickers" not in payload:
            raise ValueError(
                f"{path}: expected key 'candidate_tickers' or a JSON list of tickers"
            )
        tickers = payload["candidate_tickers"]
    elif isinstance(payload, list):
        tickers = payload
    else:
        raise ValueError(f"{path}: expected JSON object or list, got {type(payload).__name__}")
    if not isinstance(tickers, list) or not tickers:
        raise ValueError(f"{path}: ticker list must be a non-empty JSON array")
    cleaned = [str(t).strip().upper() for t in tickers]
    if any(not t for t in cleaned):
        raise ValueError(f"{path}: blank ticker entries are not allowed")
    return frozenset(cleaned)


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
    training_universe: frozenset[str] | None = None,
    finbert_batch_size: int = 16,
) -> pd.DataFrame:
    if skip_download:
        csv_path = discover_news_csv(raw_dir)
    else:
        csv_path = ensure_kaggle_download(raw_dir)

    sampled, stats = load_filter_dedup_sample(
        csv_path,
        target_rows=target_rows,
        random_seed=random_seed,
        training_universe=training_universe,
    )
    print(
        f"ingest: raw={stats.rows_raw} universe={stats.rows_universe} "
        f"dedup={stats.rows_after_dedup} sampled={stats.rows_sampled} "
        f"oou_dropped={stats.oou_dropped} missing_dropped={stats.missing_fields_dropped}"
    )
    if training_universe is None:
        print("training_universe=default(TICKER_UNIVERSE)")
    else:
        print(f"training_universe=explicit n={len(training_universe)}")
    print(f"csv_discovered={csv_path}")
    if stats.alias_rule_version == "off":
        print("NOTE: archive aliases off (honesty / test path)")
    elif stats.alias_applied_counts:
        print(
            f"documented aliases applied ({stats.alias_rule_version}): "
            f"{stats.alias_applied_counts}"
        )
    else:
        print(f"documented aliases on ({stats.alias_rule_version}): none matched CSV")
    if stats.universe_tickers_absent:
        print(
            "WARNING: universe tickers with 0 rows after filter "
            f"(absent in archive / after documented aliases): "
            f"{list(stats.universe_tickers_absent)}"
        )
    if stats.alias_candidates_oou:
        print(
            "NOTE: unapplied OOU rename candidates (aliases off or not in registry): "
            f"{stats.alias_candidates_oou}"
        )

    closer = fetch_closes or make_cached_close_fetcher()

    rows: list[dict[str, Any]] = []
    dropped_label = 0
    for r in sampled.itertuples(index=False):
        published_at = getattr(r, "published_at_parsed", None)
        if published_at is None or (isinstance(published_at, float) and pd.isna(published_at)):
            published_at = published_at_from_calendar_date(r.calendar_date)
        feats = compute_features_and_label(
            ticker=str(r.ticker),
            published_at=published_at,
            fetch_closes=closer,
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
        raise RuntimeError(_alias_fail_closed_message(stats))

    df = pd.DataFrame(rows)
    print(f"asof_label_join: kept={len(df)} dropped_no_closes_or_label={dropped_label}")
    if skip_finbert:
        if out_path == DEFAULT_OUT or "training_events.parquet" in out_path.name:
            raise RuntimeError(
                "--skip-finbert cannot write the canonical training_events.parquet. "
                "Pass --out to a noncanonical path (e.g. data/derived/training_events_dev_nofinbert.parquet)."
            )
        df["finbert_sentiment"] = 0.0
        print("WARNING: skip_finbert=True — noncanonical output only")
    else:
        print(
            "FinBERT batch: prefer Kafka/Qdrant/Ollama down (resource_mode=finbert_train)"
        )
        df["finbert_sentiment"] = score_headlines(
            df["headline"].tolist(), batch_size=finbert_batch_size
        )

    # Served = original serving contract (TICKER_UNIVERSE), not the training expand set.
    df["served_universe"] = df["ticker"].isin(TICKER_UNIVERSE)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"missing columns: {missing}")
    df = df[OUTPUT_COLUMNS]

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
    print(
        f"served_universe rows={int(df['served_universe'].sum())} "
        f"non_served={int((~df['served_universe']).sum())}"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    df.to_parquet(tmp_path, index=False)
    tmp_path.replace(out_path)
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
    p.add_argument(
        "--training-universe-file",
        type=Path,
        default=None,
        help=(
            "JSON with candidate_tickers list (training-only expand). "
            "Default None keeps TICKER_UNIVERSE byte-identical path."
        ),
    )
    p.add_argument(
        "--finbert-batch-size",
        type=int,
        default=16,
        help="FinBERT batch size (default 16; safer on 16GB unified memory)",
    )
    args = p.parse_args(argv)
    training_universe: frozenset[str] | None = None
    if args.training_universe_file is not None:
        training_universe = load_training_universe_file(args.training_universe_file)
    try:
        build_training_events(
            raw_dir=args.raw_dir,
            out_path=args.out,
            target_rows=args.target_rows,
            random_seed=args.seed,
            allow_shortfall=args.allow_shortfall,
            skip_download=args.skip_download,
            skip_finbert=args.skip_finbert,
            training_universe=training_universe,
            finbert_batch_size=args.finbert_batch_size,
        )
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
