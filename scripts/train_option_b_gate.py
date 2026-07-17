"""CLI: train Option B downside-risk XGBoost gate (Guide 05b)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alphaguard.ml.train_option_b import (
    DEFAULT_BUNDLE,
    DEFAULT_PARQUET,
    DEFAULT_RUNS,
    TrainError,
    train_option_b,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train Option B XGBoost gate bundle")
    parser.add_argument(
        "--parquet",
        type=Path,
        default=DEFAULT_PARQUET,
        help="Path to training_events.parquet",
    )
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=DEFAULT_BUNDLE,
        help="Output model bundle directory",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS,
        help="Directory for run summary JSON",
    )
    args = parser.parse_args(argv)
    try:
        manifest = train_option_b(
            parquet=args.parquet,
            bundle_dir=args.bundle_dir,
            runs_dir=args.runs_dir,
        )
    except TrainError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    metrics = manifest.metrics
    print(
        f"ok bundle_kind={manifest.bundle_kind} "
        f"threshold={manifest.score_threshold:.4f} "
        f"test_f1={metrics.get('test_f1')} "
        f"winner={metrics.get('hpo', {}).get('winner')} "
        f"out={args.bundle_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
