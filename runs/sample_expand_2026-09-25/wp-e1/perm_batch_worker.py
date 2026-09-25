#!/usr/bin/env python3
"""Run a contiguous batch of group-label permutations; append to checkpoint.

Usage: perm_batch_worker.py START END
  START inclusive, END exclusive. Uses per-index RNG(10000+i).
"""
from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

ROOT = Path("/Users/tom/Documents/Git/alphaguard-wt-option-b")
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.thread_limits import apply_native_thread_limits
apply_native_thread_limits()

import numpy as np
import pandas as pd
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_calibration import ProbabilityCalibrator
from alphaguard.ml.study_metrics import compute_metrics_suite
from alphaguard.ml.study_walkforward import (
    apply_trading_day_embargo,
    expanding4_folds,
    _session_indices,
)
from alphaguard.ml.train_eval import fit_threshold_train_f1
from alphaguard.ml.train_hpo import FIXED_PARAMS

OUT = ROOT / "runs/sample_expand_2026-09-25/wp-e1"
FREEZE = ROOT / "data/derived/training_events_optionB_001856a6.parquet"
LOCKED_START = 7125
CKPT = OUT / "permutation_checkpoint.json"
N_PERMS = 200

MAX_DEPTH = 2
ETA = 0.1
NUM_BOOST_ROUND = 40
SCALE_POS_WEIGHT = 2.0
CALIBRATION = "isotonic"


def load_dev():
    raw = pd.read_parquet(FREEZE)
    df = raw.iloc[:LOCKED_START].copy().reset_index(drop=True)
    del raw
    return df


def fold3(df_dev):
    n_dev = len(df_dev)
    folds, locked, src = expanding4_folds(n_dev + 1, train_frac=0.8, n_dev=n_dev)
    feat, lab = _session_indices(df_dev)
    folds, _ = apply_trading_day_embargo(folds, lab, feat)
    return folds[3]


def fit_score(x_tr, y_tr, x_va, y_va, seed=0):
    names = list(FEATURE_NAMES)
    params = {**FIXED_PARAMS, "seed": int(seed), "max_depth": MAX_DEPTH, "eta": ETA,
              "scale_pos_weight": SCALE_POS_WEIGHT, "nthread": 1}
    dtrain = xgb.DMatrix(x_tr, label=y_tr, feature_names=names)
    booster = xgb.train(params, dtrain, num_boost_round=NUM_BOOST_ROUND)
    raw_tr = booster.predict(dtrain)
    cal = ProbabilityCalibrator(CALIBRATION)  # type: ignore[arg-type]
    cal.fit(raw_tr, y_tr)
    train_probs = cal.predict_proba(raw_tr)
    thr = float(fit_threshold_train_f1(y_tr, train_probs))
    dval = xgb.DMatrix(x_va, feature_names=names)
    val_probs = cal.predict_proba(booster.predict(dval))
    va = compute_metrics_suite(y_va, val_probs, threshold=thr, beta=1.0)
    del booster, dtrain, dval
    gc.collect()
    return float(va["auprc"])


def ticker_day_ids(df):
    keys = list(zip(df["ticker"].astype(str), pd.to_datetime(df["feature_as_of"]).astype("int64")))
    codes, _ = pd.factorize(pd.Series(keys), sort=False)
    return codes.astype(np.int64)


def permute(y, g, rng):
    uniq = np.unique(g)
    glabel = {}
    for gg in uniq:
        vals = y[g == gg]
        glabel[int(gg)] = int(vals.sum() * 2 >= len(vals))
    labels = np.array([glabel[int(gg)] for gg in uniq], dtype=y.dtype)
    rng.shuffle(labels)
    mapped = {int(gg): int(lab) for gg, lab in zip(uniq, labels)}
    return np.array([mapped[int(gg)] for gg in g], dtype=y.dtype)


def main():
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    assert 0 <= start < end <= N_PERMS

    df = load_dev()
    f3 = fold3(df)
    names = list(FEATURE_NAMES)
    x_all = df[names].to_numpy(float)
    y_all = df["label_high_risk"].to_numpy(int)
    x_tr = x_all[: f3.train_end]
    y_tr = y_all[: f3.train_end]
    x_va = x_all[f3.val_start : f3.val_end]
    y_va = y_all[f3.val_start : f3.val_end]
    g_tr = ticker_day_ids(df.iloc[: f3.train_end])
    prev = float(y_va.mean())

    if CKPT.exists():
        ckpt = json.loads(CKPT.read_text())
        nulls = [float(x) for x in ckpt["null_scores"]]
        observed = float(ckpt.get("observed_val_auprc", ckpt.get("observed_auprc", 0.0)))
    else:
        nulls = []
        observed = fit_score(x_tr, y_tr, x_va, y_va, seed=0)

    # Ensure nulls list length == start (pad/truncate carefully)
    if len(nulls) < start:
        raise SystemExit(f"checkpoint has {len(nulls)} scores but start={start}")
    nulls = nulls[:start]

    print(f"batch [{start},{end}) observed={observed:.6f} resume_len={len(nulls)}", flush=True)
    for i in range(start, end):
        rng = np.random.default_rng(10_000 + i)
        y_perm = permute(y_tr, g_tr, rng)
        try:
            score = fit_score(x_tr, y_perm, x_va, y_va, seed=0)
        except Exception as exc:
            print(f"  perm {i} FAIL {type(exc).__name__}: {exc}", flush=True)
            score = prev
        nulls.append(float(score))
        gc.collect()
        if (i + 1) % 5 == 0 or (i + 1) == end:
            print(f"  perm {i+1}/{N_PERMS} last={score:.4f}", flush=True)
            CKPT.write_text(json.dumps({
                "n_done": len(nulls),
                "observed_val_auprc": observed,
                "null_scores": nulls,
            }, indent=2))

    print(f"batch done [{start},{end}) n_done={len(nulls)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
