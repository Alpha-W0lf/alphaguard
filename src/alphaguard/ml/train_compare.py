"""JH-63.1 — same-booster A/B of threshold fittings on a frozen test."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.train_eval import (
    THRESHOLD_TRAIN_F1,
    THRESHOLD_TRAIN_VAL_FBETA,
    resolve_threshold,
    split_metrics,
    train_val_slices,
)
from alphaguard.ml.train_option_b import (
    DEFAULT_PARQUET,
    DEFAULT_RUNS,
    PreparedTrain,
    dataset_hash,
    prepare_trained_split,
    write_run_summary,
)

PUBLISHED_BASELINE_F1 = 0.087
PUBLISHED_BASELINE_PRECISION = 0.05
PASS_PRECISION = 0.15
PASS_F1 = 0.20
SOFT_FP_MAX = 8
SOFT_F1 = 0.12
FAIL_PRECISION = 0.08


def _slice_metrics(
    prepared: PreparedTrain, threshold: float, which: str
) -> dict[str, Any]:
    split = prepared.split
    if which == "train":
        return split_metrics(split.y_train, prepared.train_probs, threshold)
    if which == "test":
        return split_metrics(split.y_test, prepared.test_probs, threshold)
    if which == "val":
        _, val = train_val_slices(len(split.y_train))
        return split_metrics(split.y_train[val], prepared.train_probs[val], threshold)
    raise ValueError(f"unknown split {which}")


def method_block(prepared: PreparedTrain, method: str) -> dict[str, Any]:
    threshold, used, fallback = resolve_threshold(
        method, prepared.split.y_train, prepared.train_probs
    )
    _, val = train_val_slices(len(prepared.split.y_train))
    return {
        "threshold_fitting_requested": method,
        "threshold_fitting": used,
        "threshold_fallback_reason": fallback,
        "score_threshold": threshold,
        "train": _slice_metrics(prepared, threshold, "train"),
        "val": _slice_metrics(prepared, threshold, "val"),
        "test": _slice_metrics(prepared, threshold, "test"),
        "n_pos_test": int(prepared.split.y_test.sum()),
        "n_pos_val": int(prepared.split.y_train[val].sum()),
    }


def jh63_verdict(test_m: dict[str, Any]) -> str:
    precision = float(test_m["precision"])
    f1 = float(test_m["f1"])
    fp = int(test_m["fp"])
    if precision >= PASS_PRECISION and f1 >= PASS_F1:
        return "PASS"
    if f1 <= PUBLISHED_BASELINE_F1 or precision < FAIL_PRECISION:
        return "FAIL"
    if fp <= SOFT_FP_MAX and f1 >= SOFT_F1:
        return "SOFT_PASS"
    return "NO_GO"


def compare_threshold_fittings(
    parquet: Path = DEFAULT_PARQUET,
    runs_dir: Path = DEFAULT_RUNS,
    prepared: PreparedTrain | None = None,
) -> dict[str, Any]:
    """Train once (or reuse prepared); score both fittings on the same frozen test."""
    if prepared is None:
        prepared = prepare_trained_split(parquet)
    split = prepared.split
    x_all = prepared.df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = prepared.df["label_high_risk"].to_numpy(dtype=int)
    baseline = method_block(prepared, THRESHOLD_TRAIN_F1)
    candidate = method_block(prepared, THRESHOLD_TRAIN_VAL_FBETA)
    created = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "experiment": "jh63.1",
        "created_at": created.isoformat(),
        "parquet": str(parquet),
        "dataset_hash": dataset_hash(x_all, y_all),
        "n_train": int(len(split.y_train)),
        "n_test": int(len(split.y_test)),
        "n_positive_train": prepared.n_pos,
        "n_positive_test": int(split.y_test.sum()),
        "published_baseline": {
            "test_f1": PUBLISHED_BASELINE_F1,
            "test_precision": PUBLISHED_BASELINE_PRECISION,
            "confusion": {"tp": 1, "fp": 19, "tn": 78, "fn": 2},
            "note": "docs/FINANCE_HONESTY.md 2026-07-21 alias-rebuild manifest",
        },
        "same_run": {
            THRESHOLD_TRAIN_F1: baseline,
            THRESHOLD_TRAIN_VAL_FBETA: candidate,
        },
        "acceptance": {
            "rules": {
                "PASS": "locked-test precision>=0.15 and F1>=0.20",
                "SOFT_PASS": "FP<=8 and F1>=0.12 but below PASS",
                "FAIL": "F1<=0.087 or precision<0.08",
            },
            "verdict": jh63_verdict(candidate["test"]),
            "candidate_vs_same_run_baseline_f1": (
                float(candidate["test"]["f1"]) - float(baseline["test"]["f1"])
            ),
        },
        "hpo_winner": prepared.hpo["winner"],
    }
    stamp = created.strftime("%Y%m%dT%H%M%SZ")
    write_run_summary(runs_dir / f"jh63_threshold_compare_{stamp}.json", payload)
    return payload
