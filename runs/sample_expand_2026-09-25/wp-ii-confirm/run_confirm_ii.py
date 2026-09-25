#!/usr/bin/env python3
"""JH-63 path (ii) confirmatory eval — ONE look on holdout B under locked selection rule.

Pre-reg: custom_resumes/docs/backlog/2026-09-25_jh63_selection_rule_holdout_prereg.md
  self-SHA256 5fbae0d07f50714211eb6a79a1e6b6fe1d5a5657f1e1959562d6338260514b6d
Holdout B tickers canonical SHA256 1b107bb20f4f5b0d9cb9f4194cf320688be8d9654a9c2e4a084bc25e20a93f2f

Rule: max F1 on inner-val subject to P>=0.25; else no operable point -> Fail.
Floors on holdout B (per seed): F1>=0.30 · P>=0.25 · AUPRC>=0.18
Go only if all seeds 42/7/123 clear floors under the rule. No shopping.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, precision_recall_curve

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_calibration import ProbabilityCalibrator
from alphaguard.ml.study_walkforward import (
    SPLIT_POLICY_NESTED_V1_DATE_ANCHOR,
    _session_indices,
    prefix_end_before_session,
    resolve_locked_test_boundary,
)
from alphaguard.ml.train_eval import (
    THRESHOLD_GRID,
    classification_counts,
    prf1,
    train_val_sizes,
)
from alphaguard.ml.train_option_b import dataset_hash, load_training_frame

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATASET = ROOT / "data/derived/training_events_jh63e_ecb73eca.parquet"
EXPECTED_HASH = "2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528"
TICKER_JSON = Path(
    "/Users/tom/Documents/Git/custom_resumes/docs/backlog/"
    "2026-09-25_jh63_selection_rule_holdout_B_tickers.json"
)
PREREG_PATH = Path(
    "/Users/tom/Documents/Git/custom_resumes/docs/backlog/"
    "2026-09-25_jh63_selection_rule_holdout_prereg.md"
)
PREREG_SELF_SHA = "5fbae0d07f50714211eb6a79a1e6b6fe1d5a5657f1e1959562d6338260514b6d"
TICKER_LIST_CANONICAL_SHA = (
    "1b107bb20f4f5b0d9cb9f4194cf320688be8d9654a9c2e4a084bc25e20a93f2f"
)

SEEDS = (42, 7, 123)
NUM_BOOST_ROUND = 40
VAL_FRAC = 0.2
MIN_PRECISION = 0.25
FLOORS = {"f1": 0.30, "precision": 0.25, "auprc": 0.18}

XGB_PARAMS_BASE = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "max_depth": 2,
    "eta": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "min_child_weight": 1,
    "scale_pos_weight": 2.0,
    "nthread": 1,
}

# Published E4 served locked-test (regression quote only; never Go).
E4_PUBLISHED_SERVED = {
    7: {"f1": 0.2488, "precision": 0.1421, "recall": 1.0, "auprc": 0.1572, "threshold": 0.15},
    42: {"f1": 0.2460, "precision": 0.1403, "recall": 1.0, "auprc": 0.1648, "threshold": 0.15},
    123: {"f1": 0.2467, "precision": 0.1407, "recall": 1.0, "auprc": 0.2031, "threshold": 0.15},
}

CT = ZoneInfo("America/Chicago")


def _now_ct() -> str:
    return datetime.now(CT).strftime("%Y-%m-%d %I:%M %p CT")


def verify_prereg_self_hash() -> str:
    text = PREREG_PATH.read_text(encoding="utf-8")
    pending = text.replace(PREREG_SELF_SHA, "CONTENT_SHA256_PENDING")
    import hashlib

    h = hashlib.sha256(pending.encode("utf-8")).hexdigest()
    if h != PREREG_SELF_SHA:
        raise RuntimeError(f"pre-reg self-hash mismatch: got {h}")
    return h


def verify_ticker_canonical(tickers: list[str]) -> str:
    import hashlib

    body = "\n".join(tickers) + "\n"
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if h != TICKER_LIST_CANONICAL_SHA:
        raise RuntimeError(f"ticker canonical SHA mismatch: got {h}")
    return h


def fit_xgb(x: np.ndarray, y: np.ndarray, seed: int) -> xgb.Booster:
    params = {**XGB_PARAMS_BASE, "seed": seed}
    dtrain = xgb.DMatrix(x, label=y, feature_names=list(FEATURE_NAMES))
    return xgb.train(params, dtrain, num_boost_round=NUM_BOOST_ROUND)


def predict_xgb(booster: xgb.Booster, x: np.ndarray) -> np.ndarray:
    return booster.predict(xgb.DMatrix(x, feature_names=list(FEATURE_NAMES)))


def pick_threshold_max_f1_s_t_precision(
    y_val: np.ndarray,
    p_val: np.ndarray,
    *,
    min_precision: float = MIN_PRECISION,
) -> dict:
    """Locked rule §2.1: max F1 among thresholds with P>=min_precision.

    Sweep = same nested harness THRESHOLD_GRID used by train_val_fbeta.
    Ties → higher threshold / lower recall (per pre-reg; differs from fbeta
    lower-threshold tie-break). Empty eligible set → no operable point.
    """
    if len(y_val) != len(p_val):
        raise ValueError("y_val/p_val length mismatch")
    if len(np.unique(y_val)) < 2:
        return {
            "operable": False,
            "reason": "val labels have <2 classes",
            "threshold": None,
            "val_f1": None,
            "val_precision": None,
            "val_recall": None,
            "n_eligible": 0,
        }

    eligible: list[tuple[float, float, float, float]] = []  # (f1, thr, p, r)
    for t in THRESHOLD_GRID:
        pred = (p_val >= t).astype(int)
        counts = classification_counts(y_val, pred)
        precision, recall, f1 = prf1(counts)
        if precision >= min_precision:
            eligible.append((float(f1), float(t), float(precision), float(recall)))

    if not eligible:
        # Report unconstrained F1-max for transparency only — NOT used.
        best_t, best_f1, best_p, best_r = None, -1.0, None, None
        for t in THRESHOLD_GRID:
            pred = (p_val >= t).astype(int)
            precision, recall, f1 = prf1(classification_counts(y_val, pred))
            if f1 > best_f1 or (f1 == best_f1 and (best_t is None or t < best_t)):
                best_f1, best_t, best_p, best_r = f1, float(t), precision, recall
        return {
            "operable": False,
            "reason": f"no threshold on THRESHOLD_GRID with P>={min_precision}",
            "threshold": None,
            "val_f1": None,
            "val_precision": None,
            "val_recall": None,
            "n_eligible": 0,
            "unconstrained_f1_max_report_only": {
                "threshold": best_t,
                "f1": float(best_f1) if best_t is not None else None,
                "precision": best_p,
                "recall": best_r,
                "note": "NOT used for Go; report-only transparency",
            },
        }

    # argmax F1; ties → higher threshold
    best_f1 = max(e[0] for e in eligible)
    tied = [e for e in eligible if abs(e[0] - best_f1) < 1e-15]
    # higher threshold
    chosen = max(tied, key=lambda e: e[1])
    f1, thr, precision, recall = chosen
    return {
        "operable": True,
        "reason": None,
        "threshold": thr,
        "val_f1": f1,
        "val_precision": precision,
        "val_recall": recall,
        "n_eligible": len(eligible),
    }


def score_at_threshold(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    pred = (p >= threshold).astype(int)
    counts = classification_counts(y, pred)
    precision, recall, f1 = prf1(counts)
    auprc = float(average_precision_score(y, p)) if len(np.unique(y)) >= 2 else float("nan")
    base = float(y.mean()) if len(y) else 0.0
    return {
        "n": int(len(y)),
        "n_pos": int(y.sum()),
        "base_rate": base,
        "threshold": float(threshold),
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "auprc": auprc,
        "lift_precision": (float(precision) / base) if base > 0 else float("nan"),
        "lift_auprc": (auprc / base) if base > 0 and not np.isnan(auprc) else float("nan"),
        **counts,
    }


def floors_clear(metrics: dict) -> tuple[bool, list[str]]:
    failed = []
    if metrics["f1"] < FLOORS["f1"]:
        failed.append(f"f1 ({metrics['f1']:.4f} < {FLOORS['f1']})")
    if metrics["precision"] < FLOORS["precision"]:
        failed.append(f"precision ({metrics['precision']:.4f} < {FLOORS['precision']})")
    if metrics["auprc"] < FLOORS["auprc"]:
        failed.append(f"auprc ({metrics['auprc']:.4f} < {FLOORS['auprc']})")
    return (len(failed) == 0), failed


def run_seed(
    seed: int,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_holdout: np.ndarray,
    y_holdout: np.ndarray,
    x_served: np.ndarray,
    y_served: np.ndarray,
) -> dict:
    t0 = time.time()
    n_fit, n_val = train_val_sizes(len(y_train), val_frac=VAL_FRAC)
    x_fit, y_fit = x_train[:n_fit], y_train[:n_fit]
    x_val, y_val = x_train[n_fit:], y_train[n_fit:]

    # Main booster on full (filtered) train — mirrors study_executor.
    main = fit_xgb(x_train, y_train, seed)

    # Aux booster on fit prefix for calibration + threshold (same as executor).
    aux = fit_xgb(x_fit, y_fit, seed)
    raw_val = predict_xgb(aux, x_val)
    calibrator = ProbabilityCalibrator("isotonic")
    if len(np.unique(y_val)) >= 2:
        calibrator.fit(raw_val, y_val)
    else:
        raw_train = predict_xgb(main, x_train)
        calibrator.fit(raw_train, y_train)

    val_probs = calibrator.predict_proba(raw_val)
    pick = pick_threshold_max_f1_s_t_precision(y_val, val_probs, min_precision=MIN_PRECISION)

    result: dict = {
        "seed": seed,
        "n_train": int(len(y_train)),
        "n_fit": int(n_fit),
        "n_val": int(n_val),
        "n_pos_train": int(y_train.sum()),
        "n_pos_val": int(y_val.sum()),
        "operable_point": bool(pick["operable"]),
        "operable_reason": pick.get("reason"),
        "val_pick": {
            "threshold": pick.get("threshold"),
            "f1": pick.get("val_f1"),
            "precision": pick.get("val_precision"),
            "recall": pick.get("val_recall"),
            "n_eligible": pick.get("n_eligible"),
        },
        "wall_time_s": None,
    }
    if "unconstrained_f1_max_report_only" in pick:
        result["unconstrained_f1_max_report_only"] = pick["unconstrained_f1_max_report_only"]

    if not pick["operable"]:
        result["holdout"] = None
        result["served_regression_only"] = None
        result["floors_clear"] = False
        result["failed_floors"] = ["no operable point on inner val"]
        result["seed_verdict"] = "FAIL"
        result["wall_time_s"] = round(time.time() - t0, 3)
        return result

    thr = float(pick["threshold"])
    # Score holdout with main booster + calibrator (executor pattern).
    holdout_raw = predict_xgb(main, x_holdout)
    holdout_p = calibrator.predict_proba(holdout_raw)
    holdout_m = score_at_threshold(y_holdout, holdout_p, thr)
    clear, failed = floors_clear(holdout_m)

    # Served regression-only (same model/threshold; NOT a Go set).
    served_raw = predict_xgb(main, x_served)
    served_p = calibrator.predict_proba(served_raw)
    served_m = score_at_threshold(y_served, served_p, thr)

    result["holdout"] = holdout_m
    result["served_regression_only"] = served_m
    result["floors_clear"] = bool(clear)
    result["failed_floors"] = failed
    result["seed_verdict"] = "PASS" if clear else "FAIL"
    result["wall_time_s"] = round(time.time() - t0, 3)
    return result


def main() -> int:
    t_all = time.time()
    print(f"[wp-ii-confirm] start {_now_ct()}", flush=True)

    prereg_sha = verify_prereg_self_hash()
    ticker_meta = json.loads(TICKER_JSON.read_text(encoding="utf-8"))
    holdout_tickers = list(ticker_meta["holdout_tickers_sorted"])
    ticker_sha = verify_ticker_canonical(holdout_tickers)
    print(f"pre-reg self-SHA OK {prereg_sha}", flush=True)
    print(f"ticker canonical SHA OK {ticker_sha}", flush=True)
    print(f"holdout tickers ({len(holdout_tickers)}): {holdout_tickers}", flush=True)

    df = load_training_frame(DATASET)
    names = list(FEATURE_NAMES)
    x_all = df[names].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    actual_hash = dataset_hash(x_all, y_all)
    if actual_hash != EXPECTED_HASH:
        raise RuntimeError(f"dataset hash mismatch: {actual_hash}")
    print(f"dataset hash OK {actual_hash}", flush=True)

    boundary = resolve_locked_test_boundary(
        df, train_frac=0.8, split_policy=SPLIT_POLICY_NESTED_V1_DATE_ANCHOR
    )
    indexed = _session_indices(df)
    if indexed is None:
        raise RuntimeError("session indices required for purge-aligned nested split")
    feature_idx, label_end_idx = indexed
    next_session = int(np.min(feature_idx[boundary:]))
    train_end = prefix_end_before_session(
        label_end_idx, candidate_end=boundary, next_session=next_session
    )
    print(
        f"boundary={boundary} train_end={train_end} dropped={boundary - train_end}",
        flush=True,
    )
    if boundary != 189362 or train_end != 188579:
        raise RuntimeError(
            f"freeze geometry drift: expected boundary=189362 train_end=188579, "
            f"got {boundary}/{train_end}"
        )

    holdout_set = set(holdout_tickers)
    # Holdout B eval = locked-window-only rows for the 20 holdout tickers.
    holdout_mask = (np.arange(len(df)) >= boundary) & df["ticker"].isin(holdout_set).to_numpy()
    n_holdout = int(holdout_mask.sum())
    n_holdout_pos = int(y_all[holdout_mask].sum())
    print(f"holdout B eval n={n_holdout} pos={n_holdout_pos}", flush=True)
    if n_holdout != 1925 or n_holdout_pos != 644:
        raise RuntimeError(
            f"holdout size mismatch: expected n=1925 pos=644, got {n_holdout}/{n_holdout_pos}"
        )

    # Train = purged train prefix EXCLUDING holdout tickers (all rows of those names).
    train_idx = np.arange(train_end)
    train_keep = ~df.iloc[:train_end]["ticker"].isin(holdout_set).to_numpy()
    train_idx = train_idx[train_keep]
    print(
        f"train after excluding holdout tickers: n={len(train_idx)} "
        f"(excluded {int((~train_keep).sum())} rows from [:train_end))",
        flush=True,
    )

    # Served locked-test (regression only).
    test_df = df.iloc[boundary:]
    served_mask_in_test = test_df["served_universe"].astype(bool).to_numpy()
    served_idx = np.arange(boundary, len(df))[served_mask_in_test]
    print(
        f"served locked-test (regression only) n={len(served_idx)} "
        f"pos={int(y_all[served_idx].sum())}",
        flush=True,
    )

    x_train = x_all[train_idx]
    y_train = y_all[train_idx]
    x_holdout = x_all[holdout_mask]
    y_holdout = y_all[holdout_mask]
    x_served = x_all[served_idx]
    y_served = y_all[served_idx]

    seed_results = []
    for seed in SEEDS:
        print(f"--- seed {seed} ---", flush=True)
        r = run_seed(seed, x_train, y_train, x_holdout, y_holdout, x_served, y_served)
        seed_results.append(r)
        op = r["operable_point"]
        if op and r["holdout"] is not None:
            h = r["holdout"]
            print(
                f"  operable thr={r['val_pick']['threshold']:.4f} "
                f"valF1={r['val_pick']['f1']:.4f} valP={r['val_pick']['precision']:.4f} "
                f"| holdout F1={h['f1']:.4f} P={h['precision']:.4f} R={h['recall']:.4f} "
                f"AUPRC={h['auprc']:.4f} → {r['seed_verdict']}",
                flush=True,
            )
        else:
            print(
                f"  NO OPERABLE POINT ({r.get('operable_reason')}) → {r['seed_verdict']}",
                flush=True,
            )

    all_pass = all(r["seed_verdict"] == "PASS" for r in seed_results)
    go_claimed = bool(all_pass)
    study_verdict = "PASS" if all_pass else "FAIL"

    payload = {
        "schema": "jh63_path_ii_confirm_holdout_B_v1",
        "stamp_america_chicago": _now_ct(),
        "worktree": str(ROOT),
        "machine": "Toms-MB-Pro-M2-Pro (75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c)",
        "routing": "local · workers=1 · OMP_NUM_THREADS=1 · no CloudAgent",
        "prereg": {
            "path": str(PREREG_PATH),
            "self_sha256": prereg_sha,
            "holdout": "B",
            "selection_rule": "max F1 on inner-val subject to P>=0.25; else no operable point Fail",
            "ticker_list_canonical_sha256": ticker_sha,
            "ticker_json": str(TICKER_JSON),
        },
        "freeze": {
            "dataset_path": str(DATASET),
            "dataset_hash": actual_hash,
            "label": "fwd_return_5d < -0.03 (label_high_risk, -3%/5d)",
            "features": names,
            "xgb": {**XGB_PARAMS_BASE, "num_boost_round": NUM_BOOST_ROUND},
            "calibration": "isotonic",
            "split_policy": SPLIT_POLICY_NESTED_V1_DATE_ANCHOR,
            "boundary_index": boundary,
            "train_end_purged": train_end,
            "seeds": list(SEEDS),
            "threshold_sweep": "THRESHOLD_GRID 0.05..0.95 step 0.05 (nested harness)",
            "tie_break": "higher threshold / lower recall among equal F1",
        },
        "holdout_B": {
            "tickers": holdout_tickers,
            "n": n_holdout,
            "n_pos": n_holdout_pos,
            "base_rate": float(y_holdout.mean()),
            "eval_slice": "locked-window-only (index >= boundary) on holdout tickers",
            "train_policy": "holdout tickers removed from purged train prefix",
            "n_train_after_exclude": int(len(train_idx)),
        },
        "floors": FLOORS,
        "seeds": seed_results,
        "study_verdict": study_verdict,
        "model_quality_go_claimed": go_claimed,
        "e4_served_published_regression_quote": E4_PUBLISHED_SERVED,
        "anti_shopping": {
            "one_look": True,
            "second_threshold": False,
            "label_change": False,
            "feature_add": False,
            "ticker_redraw": False,
            "served_used_for_go": False,
        },
        "wall_time_s": round(time.time() - t_all, 3),
    }

    metrics_path = OUT / "metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {metrics_path}", flush=True)

    # summary.md
    lines = []
    lines.append("# WP-ii-confirm — JH-63 path (ii) confirmatory eval (holdout B)")
    lines.append("")
    lines.append(f"**Status:** COMPLETE · **{study_verdict}** · model_quality_go_claimed=**{str(go_claimed).lower()}**")
    lines.append(f"**Stamp:** {_now_ct()} (America/Chicago)")
    lines.append(f"**Worktree:** `{ROOT}`")
    lines.append("**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)")
    lines.append("**Routing:** Local · `OMP_NUM_THREADS=1` · workers=1 · no CloudAgent")
    lines.append("**Uncommitted:** leave uncommitted")
    lines.append("")
    lines.append("## Locked SSOT")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|---|---|")
    lines.append(f"| Pre-reg self-SHA256 | `{prereg_sha}` |")
    lines.append(f"| Ticker-list canonical SHA256 | `{ticker_sha}` |")
    lines.append(f"| Holdout | **B** (20 expand tickers) |")
    lines.append("| Rule | max F1 on inner-val **s.t. P≥0.25**; else no-operable-point Fail |")
    lines.append(f"| Dataset hash | `{actual_hash}` |")
    lines.append(f"| Geometry | boundary={boundary} · train_end={train_end} |")
    lines.append(f"| Holdout B eval | n=**{n_holdout}** · pos=**{n_holdout_pos}** · base_rate=**{y_holdout.mean():.6f}** |")
    lines.append(f"| Train after exclude | n=**{len(train_idx)}** |")
    lines.append("| Floors | F1≥0.30 · P≥0.25 · AUPRC≥0.18 (per seed on holdout B) |")
    lines.append("| Served locked-test | regression only — not Go |")
    lines.append("")
    lines.append("## Per-seed holdout B results")
    lines.append("")
    lines.append(
        "| Seed | Operable? | thr | val F1/P/R | Holdout F1 | P | R | AUPRC | "
        "P-lift | AUPRC-lift | Verdict | Failed |"
    )
    lines.append("| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for r in seed_results:
        op = "yes" if r["operable_point"] else "no"
        if r["operable_point"] and r["holdout"]:
            h = r["holdout"]
            vp = r["val_pick"]
            val_s = f"{vp['f1']:.4f}/{vp['precision']:.4f}/{vp['recall']:.4f}"
            failed = "; ".join(r["failed_floors"]) if r["failed_floors"] else "—"
            lines.append(
                f"| {r['seed']} | {op} | {vp['threshold']:.2f} | {val_s} | "
                f"{h['f1']:.4f} | {h['precision']:.4f} | {h['recall']:.4f} | {h['auprc']:.4f} | "
                f"{h['lift_precision']:.3f}× | {h['lift_auprc']:.3f}× | **{r['seed_verdict']}** | {failed} |"
            )
        else:
            reason = r.get("operable_reason") or "no operable point"
            lines.append(
                f"| {r['seed']} | {op} | — | — | — | — | — | — | — | — | **FAIL** | {reason} |"
            )
    lines.append("")
    lines.append(f"**Study verdict: {study_verdict}** (need all three seeds PASS).")
    lines.append(f"**model_quality_go_claimed = {str(go_claimed).lower()}**")
    lines.append("")
    lines.append("## Served locked-test (regression only — not Go)")
    lines.append("")
    lines.append("| Seed | E4 published F1/P/AUPRC | This-run served F1/P/R/AUPRC (same thr) |")
    lines.append("| ---: | --- | --- |")
    for r in seed_results:
        pub = E4_PUBLISHED_SERVED[r["seed"]]
        pub_s = f"{pub['f1']:.4f}/{pub['precision']:.4f}/{pub['auprc']:.4f}"
        if r["served_regression_only"]:
            s = r["served_regression_only"]
            this_s = f"{s['f1']:.4f}/{s['precision']:.4f}/{s['recall']:.4f}/{s['auprc']:.4f}"
        else:
            this_s = "n/a (no operable thr)"
        lines.append(f"| {r['seed']} | {pub_s} | {this_s} |")
    lines.append("")
    lines.append("## Anti-shopping")
    lines.append("")
    lines.append("- One look only. No second threshold. No label change. No feature add. No ticker re-draw.")
    lines.append("- Served locked-test never counted toward Go.")
    lines.append("- Unconstrained F1-max was **not** used as fallback when eligible set empty.")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("| Item | Path |")
    lines.append("|---|---|")
    lines.append(f"| This summary | `{OUT / 'summary.md'}` |")
    lines.append(f"| Metrics JSON | `{OUT / 'metrics.json'}` |")
    lines.append(f"| Runner | `{OUT / 'run_confirm_ii.py'}` |")
    lines.append("")
    if go_claimed:
        lines.append("## Go")
        lines.append("")
        lines.append(
            "All seeds cleared holdout B floors under the locked selection rule. "
            "Go claimed for this selection-rule claim only (same label −3%/5d, same 9 features)."
        )
    else:
        lines.append("## STOP")
        lines.append("")
        lines.append(
            "Fail stands. Publish honestly. No second look / threshold / ticker re-draw / floor move."
        )
        lines.append("**Model Quality Go: UNCLAIMED.**")
    lines.append("")

    summary_path = OUT / "summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {summary_path}", flush=True)
    print(
        f"[wp-ii-confirm] done verdict={study_verdict} go_claimed={go_claimed} "
        f"wall={time.time() - t_all:.1f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
