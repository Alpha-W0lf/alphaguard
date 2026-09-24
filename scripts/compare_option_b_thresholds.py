"""CLI: JH-63.1 same-booster threshold A/B on the frozen time-ordered test."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alphaguard.ml.train_compare import compare_threshold_fittings
from alphaguard.ml.train_option_b import DEFAULT_PARQUET, DEFAULT_RUNS, TrainError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare train_f1_max vs train_val_fbeta_0.5 on one frozen test"
    )
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    args = parser.parse_args(argv)
    try:
        payload = compare_threshold_fittings(parquet=args.parquet, runs_dir=args.runs_dir)
    except TrainError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload["acceptance"], indent=2))
    same = payload["same_run"]
    for name, block in same.items():
        test = block["test"]
        print(
            f"{name}: t={block['score_threshold']:.4f} "
            f"P={test['precision']:.4f} R={test['recall']:.4f} F1={test['f1']:.4f} "
            f"TP/FP/TN/FN={test['tp']}/{test['fp']}/{test['tn']}/{test['fn']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
