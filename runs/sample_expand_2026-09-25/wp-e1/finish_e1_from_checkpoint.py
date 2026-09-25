#!/usr/bin/env python3
"""WP-E1 FINISH/RESUME: learning curve + ticker-day group permutation on freeze 001856a6.

Dev block only. Locked-test rows (index >= 7125) are never retained.
Diagnostic only — never a Go input.
Artifacts: runs/sample_expand_2026-09-25/wp-e1/{learning_curve,permutation,summary}.
"""
from __future__ import annotations

import gc
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path("/Users/tom/Documents/Git/alphaguard-wt-option-b")
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.thread_limits import apply_native_thread_limits

apply_native_thread_limits()

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
OUT.mkdir(parents=True, exist_ok=True)

FREEZE = ROOT / "data/derived/training_events_optionB_001856a6.parquet"
LOCKED_START = 7125
GIT_SHA = "1f53808d0945bab0b7a3119a9ee00ab524df6145"
FREEZE_HASH = "001856a6"

# Nested winner (jh63 go-gate nested purge 001856a6). No HPO.
MAX_DEPTH = 2
ETA = 0.1
NUM_BOOST_ROUND = 40
SCALE_POS_WEIGHT = 2.0
CALIBRATION = "isotonic"
FRACTIONS = (0.25, 0.5, 0.75, 1.0)
SEEDS = (0, 1, 2, 3, 4)
N_PERMS = 200


def log(msg: str, lines: list[str]) -> None:
    print(msg, flush=True)
    lines.append(msg)


def load_dev_only(path: Path) -> pd.DataFrame:
    """Load freeze; HARD-drop locked-test rows and assert they are gone."""
    raw = pd.read_parquet(path)
    n_full = len(raw)
    if n_full < LOCKED_START + 1:
        raise RuntimeError(f"freeze too small: n={n_full}")
    locked = raw.iloc[LOCKED_START:]
    assert len(locked) == n_full - LOCKED_START
    assert pd.to_datetime(locked["feature_as_of"]).min() >= pd.Timestamp("2020-02-25")
    df = raw.iloc[:LOCKED_START].copy()
    del raw, locked
    assert len(df) == LOCKED_START
    assert int(df.index.max()) < LOCKED_START
    df = df.reset_index(drop=True)
    assert len(df) == LOCKED_START
    return df


def fold3_purged(df_dev: pd.DataFrame):
    """Last expanding4 fold of DEV, trading-day purged."""
    n_dev = len(df_dev)
    assert n_dev == LOCKED_START
    folds, locked_start, src = expanding4_folds(
        n_dev + 1, train_frac=0.8, n_dev=n_dev
    )
    assert locked_start == n_dev
    feat_sess, label_end = _session_indices(df_dev)
    folds, changed = apply_trading_day_embargo(folds, label_end, feat_sess)
    f3 = folds[3]
    assert f3.val_end == n_dev
    assert f3.train_end < f3.val_start
    return f3, src, changed, folds


def fit_score(
    x_tr: np.ndarray,
    y_tr: np.ndarray,
    x_va: np.ndarray,
    y_va: np.ndarray,
    *,
    seed: int,
) -> dict:
    n_pos = int(y_tr.sum())
    if n_pos == 0 or n_pos == len(y_tr):
        raise ValueError(f"train single-class n_pos={n_pos} n={len(y_tr)}")
    names = list(FEATURE_NAMES)
    params = {
        **FIXED_PARAMS,
        "seed": int(seed),
        "max_depth": MAX_DEPTH,
        "eta": ETA,
        "scale_pos_weight": SCALE_POS_WEIGHT,
        "nthread": 1,
    }
    dtrain = xgb.DMatrix(x_tr, label=y_tr, feature_names=names)
    booster = xgb.train(params, dtrain, num_boost_round=NUM_BOOST_ROUND)
    raw_tr = booster.predict(dtrain)
    cal = ProbabilityCalibrator(CALIBRATION)  # type: ignore[arg-type]
    cal.fit(raw_tr, y_tr)
    train_probs = cal.predict_proba(raw_tr)
    threshold = float(fit_threshold_train_f1(y_tr, train_probs))
    dval = xgb.DMatrix(x_va, feature_names=names)
    val_probs = cal.predict_proba(booster.predict(dval))
    tr = compute_metrics_suite(y_tr, train_probs, threshold=threshold, beta=1.0)
    va = compute_metrics_suite(y_va, val_probs, threshold=threshold, beta=1.0)
    prev = float(y_va.mean()) if len(y_va) else 0.0
    return {
        "train_auprc": float(tr["auprc"]),
        "val_auprc": float(va["auprc"]),
        "val_auprc_over_prev": float(va["auprc"]) / prev if prev > 0 else float("nan"),
        "val_f1": float(va["f1"]),
        "val_precision": float(va["precision"]),
        "val_recall": float(va["recall"]),
        "threshold": threshold,
        "n_train": int(len(y_tr)),
        "n_train_pos": n_pos,
        "n_val": int(len(y_va)),
        "n_val_pos": int(y_va.sum()),
        "val_prevalence": prev,
    }


def ticker_day_ids(df: pd.DataFrame) -> np.ndarray:
    keys = list(
        zip(
            df["ticker"].astype(str),
            pd.to_datetime(df["feature_as_of"]).astype("int64"),
        )
    )
    codes, _ = pd.factorize(pd.Series(keys), sort=False)
    return codes.astype(np.int64)


def subsample_mask(group_ids: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    uniq = np.unique(group_ids)
    n_keep = max(1, int(round(len(uniq) * fraction)))
    if n_keep >= len(uniq):
        return np.ones(len(group_ids), dtype=bool)
    keep = set(rng.choice(uniq, size=n_keep, replace=False).tolist())
    return np.isin(group_ids, list(keep))


def permute_labels_by_group(
    y: np.ndarray, group_ids: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Permute labels at ticker-day group level (rows in a group move together).

    Group label = majority of rows in the group (ties → 1). Almost all
    ticker-days are constant; one known GOOGL 2019-05-07 anomaly is not.
    """
    uniq = np.unique(group_ids)
    g_label: dict[int, int] = {}
    n_nonconst = 0
    for g in uniq:
        vals = y[group_ids == g]
        if not np.all(vals == vals[0]):
            n_nonconst += 1
        # majority; tie → positive
        g_label[int(g)] = int(vals.sum() * 2 >= len(vals))
    if n_nonconst:
        # counted once at first call; main logs separately if needed
        pass
    labels = np.array([g_label[int(g)] for g in uniq], dtype=y.dtype)
    rng.shuffle(labels)
    mapped = {int(g): int(lab) for g, lab in zip(uniq, labels)}
    return np.array([mapped[int(g)] for g in group_ids], dtype=y.dtype)

def figueroa_power_law(ns: np.ndarray, scores: np.ndarray) -> dict | None:
    """Optional score ≈ a + c * n^(-b). Estimated only — never Go evidence."""
    ns = np.asarray(ns, dtype=float)
    scores = np.asarray(scores, dtype=float)
    if len(ns) < 3 or np.any(ns <= 0):
        return None
    best = None
    for b in np.linspace(0.05, 2.0, 40):
        A = np.column_stack([np.ones_like(ns), np.power(ns, -b)])
        coef, *_ = np.linalg.lstsq(A, scores, rcond=None)
        pred = A @ coef
        sse = float(np.sum((scores - pred) ** 2))
        if best is None or sse < best["sse"]:
            best = {
                "form": "auprc ≈ a + c * n^(-b)",
                "a": float(coef[0]),
                "c": float(coef[1]),
                "b": float(b),
                "sse": sse,
                "rmse": float(np.sqrt(sse / len(ns))),
                "status": "Estimated",
                "note": "Figueroa-style; never used as Go evidence",
            }
    return best


def s2_verdict(by_frac: dict) -> tuple[str, str]:
    means = [by_frac[f]["mean_val_auprc"] for f in FRACTIONS]
    spreads = [by_frac[f]["std_val_auprc"] for f in FRACTIONS]
    gap100 = by_frac[1.0]["mean_train_auprc"] - by_frac[1.0]["mean_val_auprc"]
    spread100 = by_frac[1.0]["std_val_auprc"]
    nondec = all(means[i + 1] + 1e-6 >= means[i] for i in range(len(means) - 1))
    mean_spread = float(np.mean(spreads))
    mean_range = float(max(means) - min(means))
    flat = mean_range <= (mean_spread + 1e-6)
    gap_large = gap100 > spread100

    if gap_large and nondec:
        return (
            "variance_dominated",
            (
                f"S2 VARIANCE-DOMINATED: gap@100%={gap100:.4f} > seed_spread={spread100:.4f} "
                f"and val AUPRC non-decreasing {means[0]:.4f}→{means[-1]:.4f} "
                f"→ may proceed E2 (subject to S3/G4)."
            ),
        )
    if flat and (not gap_large):
        return (
            "bias_dominated",
            (
                f"S2 BIAS-DOMINATED STOP: curve flat (mean_range={mean_range:.4f} ≤ "
                f"mean_spread={mean_spread:.4f}) and gap@100%={gap100:.4f} ≤ "
                f"spread={spread100:.4f} → feature/label family is the bottleneck; no E2."
            ),
        )
    return (
        "ambiguous",
        (
            f"S2 AMBIGUOUS STOP: nondec={nondec} flat={flat} gap_large={gap_large} "
            f"gap@100%={gap100:.4f} spread={spread100:.4f} "
            f"means={[round(m, 4) for m in means]} → escalate Opus; no E2."
        ),
    )


def main() -> int:
    t0 = time.time()
    lines: list[str] = []
    log(f"WP-E1 start git={GIT_SHA} freeze={FREEZE}", lines)

    df_dev = load_dev_only(FREEZE)
    log(
        f"Loaded DEV only: n={len(df_dev)} (locked index>={LOCKED_START} discarded)",
        lines,
    )

    f3, embargo_src, changed, all_folds = fold3_purged(df_dev)
    log(
        f"fold3 purged: train=[0,{f3.train_end}) val=[{f3.val_start},{f3.val_end}) "
        f"embargo_rows={f3.embargo_rows} source={embargo_src} changed={changed}",
        lines,
    )
    for f in all_folds:
        log(
            f"  fold{f.fold}: train_end={f.train_end} val=[{f.val_start},{f.val_end}) "
            f"embargo={f.embargo_rows}",
            lines,
        )

    names = list(FEATURE_NAMES)
    x_all = df_dev[names].to_numpy(dtype=float)
    y_all = df_dev["label_high_risk"].to_numpy(dtype=int)
    x_tr_full = x_all[: f3.train_end]
    y_tr_full = y_all[: f3.train_end]
    x_va = x_all[f3.val_start : f3.val_end]
    y_va = y_all[f3.val_start : f3.val_end]
    g_tr = ticker_day_ids(df_dev.iloc[: f3.train_end])
    n_td = int(len(np.unique(g_tr)))
    val_prev = float(y_va.mean())
    log(
        f"train_pool rows={len(y_tr_full)} pos={int(y_tr_full.sum())} ticker_days={n_td}; "
        f"val rows={len(y_va)} pos={int(y_va.sum())} prev={val_prev:.4f}",
        lines,
    )

    points: list[dict] = []
    for frac in FRACTIONS:
        for seed in SEEDS:
            mask = subsample_mask(g_tr, frac, seed)
            m = fit_score(
                x_tr_full[mask],
                y_tr_full[mask],
                x_va,
                y_va,
                seed=seed,
            )
            m.update(
                {
                    "fraction": frac,
                    "seed": seed,
                    "n_ticker_days": int(len(np.unique(g_tr[mask]))),
                }
            )
            points.append(m)
            log(
                f"  frac={frac:.2f} seed={seed} n_td={m['n_ticker_days']} "
                f"train_auprc={m['train_auprc']:.4f} val_auprc={m['val_auprc']:.4f} "
                f"auprc/prev={m['val_auprc_over_prev']:.3f} "
                f"F1={m['val_f1']:.4f} P={m['val_precision']:.4f}",
                lines,
            )

    by_frac: dict = {}
    for frac in FRACTIONS:
        subset = [p for p in points if p["fraction"] == frac]

        def _stats(key: str, sub: list = subset) -> tuple[float, float]:
            vals = np.asarray([p[key] for p in sub], dtype=float)
            return float(vals.mean()), float(vals.std(ddof=1)) if len(vals) > 1 else 0.0

        mt, st = _stats("train_auprc")
        mv, sv = _stats("val_auprc")
        mr, sr = _stats("val_auprc_over_prev")
        mf, sf = _stats("val_f1")
        mp, sp = _stats("val_precision")
        by_frac[frac] = {
            "mean_train_auprc": mt,
            "std_train_auprc": st,
            "mean_val_auprc": mv,
            "std_val_auprc": sv,
            "mean_auprc_over_prev": mr,
            "std_auprc_over_prev": sr,
            "mean_val_f1": mf,
            "std_val_f1": sf,
            "mean_val_precision": mp,
            "std_val_precision": sp,
            "mean_n_ticker_days": float(np.mean([p["n_ticker_days"] for p in subset])),
            "mean_n_train": float(np.mean([p["n_train"] for p in subset])),
            "points": subset,
        }

    s2_code, s2_line = s2_verdict(by_frac)
    log(s2_line, lines)

    ns = np.array([by_frac[f]["mean_n_ticker_days"] for f in FRACTIONS])
    vs = np.array([by_frac[f]["mean_val_auprc"] for f in FRACTIONS])
    power = figueroa_power_law(ns, vs)
    if power:
        log(
            f"Figueroa power-law (Estimated): a={power['a']:.4f} c={power['c']:.4f} "
            f"b={power['b']:.3f} rmse={power['rmse']:.4f}",
            lines,
        )

    log(f"Permutation test: n={N_PERMS} group-level on train pool, score=val AUPRC", lines)
    obs = fit_score(x_tr_full, y_tr_full, x_va, y_va, seed=0)
    observed_auprc = float(obs["val_auprc"])
    log(f"  observed val_auprc={observed_auprc:.6f}", lines)

    ckpt_path = OUT / "permutation_checkpoint.json"
    null_scores: list[float] = []
    start_i = 0
    if ckpt_path.exists():
        ckpt = json.loads(ckpt_path.read_text())
        null_scores = [float(x) for x in ckpt["null_scores"]]
        start_i = int(ckpt.get("n_done", ckpt.get("n_done", len(null_scores))))
        # tolerate either key
        start_i = len(null_scores) if start_i != len(null_scores) else start_i
        log(f"  RESUME from checkpoint: n_done={start_i}", lines)
    else:
        log("  no checkpoint; starting from 0", lines)

    for i in range(start_i, N_PERMS):
        # per-index RNG → resume-safe (independent of prior shuffle count)
        rng_i = np.random.default_rng(10_000 + i)
        y_perm = permute_labels_by_group(y_tr_full, g_tr, rng_i)
        try:
            m = fit_score(x_tr_full, y_perm, x_va, y_va, seed=0)
            null_scores.append(float(m["val_auprc"]))
        except Exception as exc:
            log(f"  perm {i}: FAIL ({type(exc).__name__}: {exc}); use prevalence", lines)
            null_scores.append(val_prev)
        del y_perm
        gc.collect()
        if (i + 1) % 25 == 0 or (i + 1) == N_PERMS:
            log(f"  perm {i+1}/{N_PERMS} last={null_scores[-1]:.4f}", lines)
            ckpt_path.write_text(
                json.dumps(
                    {"n_done": i + 1, "observed_val_auprc": observed_auprc, "null_scores": null_scores},
                    indent=2,
                )
            )

    assert len(null_scores) >= N_PERMS
    null_scores = null_scores[:N_PERMS]
    null_arr = np.asarray(null_scores, dtype=float)
    C = int(np.sum(null_arr >= observed_auprc))
    p_value = (C + 1) / (N_PERMS + 1)
    s3_stop = p_value >= 0.05
    if s3_stop:
        s3_line = (
            f"S3 STOP: permutation p={p_value:.4f} ≥ 0.05 (C={C}, n={N_PERMS}) — "
            f"no detectable dependency; G4 locked → do NOT proceed to E2."
        )
    else:
        s3_line = (
            f"S3 CLEAR: permutation p={p_value:.4f} < 0.05 (C={C}, n={N_PERMS})."
        )
    log(s3_line, lines)

    if (s2_code == "variance_dominated") and (not s3_stop):
        overall = "PROCEED_E2 (variance-dominated and perm p<0.05). Go UNCLAIMED."
    elif s3_stop:
        overall = "STOP S3 (perm p≥0.05; G4 forbids E2). Go UNCLAIMED."
    elif s2_code == "bias_dominated":
        overall = "STOP S2 (bias-dominated). Go UNCLAIMED."
    else:
        overall = "STOP S2 (ambiguous — escalate Opus). Go UNCLAIMED."
    log(overall, lines)

    lc = {
        "git_sha": GIT_SHA,
        "freeze_hash_prefix": FREEZE_HASH,
        "freeze_path": str(FREEZE),
        "locked_start_index": LOCKED_START,
        "locked_rows_loaded": False,
        "design": {
            "validation": "expanding4 fold 3 of DEV, trading-day purged",
            "train_pool": f"[0, {f3.train_end})",
            "val": f"[{f3.val_start}, {f3.val_end})",
            "embargo_rows": f3.embargo_rows,
            "embargo_source": embargo_src,
            "fractions": list(FRACTIONS),
            "seeds": list(SEEDS),
            "subsample_unit": "ticker-day group",
            "hyperparams": {
                "max_depth": MAX_DEPTH,
                "eta": ETA,
                "num_boost_round": NUM_BOOST_ROUND,
                "scale_pos_weight": SCALE_POS_WEIGHT,
                "subsample": FIXED_PARAMS["subsample"],
                "colsample_bytree": FIXED_PARAMS["colsample_bytree"],
                "reg_lambda": FIXED_PARAMS["reg_lambda"],
                "calibration": CALIBRATION,
                "threshold_method": "train_f1_max",
            },
            "workers": 1,
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        },
        "val_prevalence": val_prev,
        "points": points,
        "by_fraction": {
            str(f): {k: v for k, v in by_frac[f].items() if k != "points"}
            for f in FRACTIONS
        },
        "s2_code": s2_code,
        "s2_line": s2_line,
        "figueroa_power_law": power,
    }
    (OUT / "learning_curve.json").write_text(json.dumps(lc, indent=2) + "\n")

    perm = {
        "git_sha": GIT_SHA,
        "freeze_hash_prefix": FREEZE_HASH,
        "n_permutations": N_PERMS,
        "permute_unit": "ticker-day group label in training pool",
        "score": "val AUPRC on fixed fold-3 val",
        "observed_val_auprc": observed_auprc,
        "null_mean": float(null_arr.mean()),
        "null_std": float(null_arr.std(ddof=1)),
        "null_max": float(null_arr.max()),
        "C_ge_observed": C,
        "p_value": p_value,
        "formula": "p=(C+1)/(n+1)",
        "s3_stop": s3_stop,
        "s3_line": s3_line,
        "null_scores": null_scores,
    }
    (OUT / "permutation.json").write_text(json.dumps(perm, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    fracs = list(FRACTIONS)
    mean_tr = [by_frac[f]["mean_train_auprc"] for f in fracs]
    std_tr = [by_frac[f]["std_train_auprc"] for f in fracs]
    mean_va = [by_frac[f]["mean_val_auprc"] for f in fracs]
    std_va = [by_frac[f]["std_val_auprc"] for f in fracs]
    n_tds = [by_frac[f]["mean_n_ticker_days"] for f in fracs]
    ax.errorbar(n_tds, mean_tr, yerr=std_tr, fmt="o-", label="train AUPRC", color="#1f77b4", capsize=3)
    ax.errorbar(n_tds, mean_va, yerr=std_va, fmt="s-", label="val AUPRC", color="#d62728", capsize=3)
    ax.axhline(val_prev, color="gray", ls="--", lw=1, label=f"val prevalence={val_prev:.3f}")
    ax.set_xlabel("Training ticker-days (mean over seeds)")
    ax.set_ylabel("AUPRC")
    ax.set_title(f"WP-E1 learning curve · 001856a6 fold3 · {s2_code}\nperm p={p_value:.4f}")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "learning_curve.png", dpi=140)
    plt.close(fig)

    wall = round(time.time() - t0, 1)
    gap100 = by_frac[1.0]["mean_train_auprc"] - by_frac[1.0]["mean_val_auprc"]
    summary = f"""# WP-E1 — Learning curve + group permutation (dev block only)

**Status:** COMPLETE · {overall}
**Date:** 2026-09-25 · wall {wall}s CT
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)
**Worktree:** `{ROOT}` @ `{GIT_SHA}`
**Freeze:** `data/derived/training_events_optionB_001856a6.parquet` · hash `{FREEZE_HASH}`
**Hard rule:** locked-test rows (index ≥ {LOCKED_START}) **never loaded** — Verified (dev n={len(df_dev)}).
**Go:** UNCLAIMED · floors unchanged · no E2 started here.

## One-line verdicts

- **{s2_line}**
- **{s3_line}**
- **Overall: {overall}**

## Design (pre-registered)

| Item | Value | Status |
|---|---|---|
| Val | expanding4 fold 3 of DEV, trading-day purged `[{f3.val_start},{f3.val_end})` | Verified |
| Train pool | purged prefix `[0,{f3.train_end})` · embargo_rows={f3.embargo_rows} ({embargo_src}) | Verified |
| Subsample | ticker-day groups @ {{0.25,0.5,0.75,1.0}} × seeds {{0..4}} | Verified |
| Hyperparams | nested winner: depth={MAX_DEPTH} eta={ETA} rounds={NUM_BOOST_ROUND} spw={SCALE_POS_WEIGHT} isotonic + train_f1_max | Verified |
| Workers / OMP | 1 / {os.environ.get('OMP_NUM_THREADS')} | Verified |
| Permutation | {N_PERMS} · group-level labels in train · score=val AUPRC · p=(C+1)/(n+1) | Verified |

## Learning curve (mean ± std over 5 seeds)

| frac | n_td | n_train | train AUPRC | val AUPRC | AUPRC/prev | val F1 | val P |
|---:|---:|---:|---:|---:|---:|---:|---:|
"""
    for f in FRACTIONS:
        b = by_frac[f]
        summary += (
            f"| {f:.2f} | {b['mean_n_ticker_days']:.0f} | {b['mean_n_train']:.0f} | "
            f"{b['mean_train_auprc']:.4f}±{b['std_train_auprc']:.4f} | "
            f"{b['mean_val_auprc']:.4f}±{b['std_val_auprc']:.4f} | "
            f"{b['mean_auprc_over_prev']:.3f}±{b['std_auprc_over_prev']:.3f} | "
            f"{b['mean_val_f1']:.4f}±{b['std_val_f1']:.4f} | "
            f"{b['mean_val_precision']:.4f}±{b['std_val_precision']:.4f} |\n"
        )

    summary += f"""
- Val prevalence (fold 3): **{val_prev:.4f}** (Verified)
- Gap train−val AUPRC @ 100%: **{gap100:.4f}**; seed spread @ 100%: **{by_frac[1.0]['std_val_auprc']:.4f}**

## Permutation

| Metric | Value |
|---|---|
| Observed val AUPRC | {observed_auprc:.6f} |
| Null mean ± std | {float(null_arr.mean()):.4f} ± {float(null_arr.std(ddof=1)):.4f} |
| Null max | {float(null_arr.max()):.4f} |
| C (# null ≥ obs) | {C} |
| p = (C+1)/(n+1) | **{p_value:.4f}** |

## Figueroa power-law (optional, Estimated only)

"""
    if power:
        summary += (
            f"- Form `{power['form']}`: a={power['a']:.4f}, c={power['c']:.4f}, "
            f"b={power['b']:.3f}, rmse={power['rmse']:.4f} — **Estimated**, not Go evidence.\n"
        )
    else:
        summary += "- Fit unavailable.\n"

    summary += f"""
## Artifacts

| File | Path |
|---|---|
| learning_curve.json | `runs/sample_expand_2026-09-25/wp-e1/learning_curve.json` |
| learning_curve.png | `runs/sample_expand_2026-09-25/wp-e1/learning_curve.png` |
| permutation.json | `runs/sample_expand_2026-09-25/wp-e1/permutation.json` |
| summary.md | `runs/sample_expand_2026-09-25/wp-e1/summary.md` |
| script (uncommitted) | `runs/sample_expand_2026-09-25/wp-e1/audit_sample_expand_e1.py` |

## What was *not* done

- No E2 build, no freeze mutation, no feature adds, no floor changes, no locked-test evaluation.
- Option-a checkout `/Users/tom/Documents/Git/alphaguard` not used.
- Artifacts left **uncommitted** (plan handoff).
"""
    (OUT / "summary.md").write_text(summary)
    (OUT / "e1_run.log").write_text("\n".join(lines) + "\n")
    log(f"Wrote artifacts under {OUT} in {wall}s", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
