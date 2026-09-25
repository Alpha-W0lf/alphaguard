#!/usr/bin/env python3
"""JH-63 Bet 1 — OOF precision-wall diagnosis (diagnosis only; no Go claim).

Frozen: dataset 2e8db9a9 / training_events_jh63e_ecb73eca.parquet,
label −3%/5d, 9 features, seeds 42/7/123, XGB params from nested Go config.
Data rule: expanding4 purged OOF on train/dev only — locked test never scored
except quoting already-published E4 numbers in summary.md.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
)

# Cap threads before heavy work (Darwin OpenMP).
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
    apply_trading_day_embargo,
    expanding4_folds,
    prefix_end_before_session,
    resolve_locked_test_boundary,
)
from alphaguard.ml.train_option_b import load_training_frame

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATASET = ROOT / "data/derived/training_events_jh63e_ecb73eca.parquet"
EXPECTED_HASH = "2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528"
SEEDS = (42, 7, 123)

# Nested Go config hparams (frozen).
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
NUM_BOOST_ROUND = 40

TEXT_FEATURES = ("finbert_sentiment",)
PRICE_FEATURES = (
    "volatility_20d",
    "return_5d_prior",
    "return_20d_prior",
    "rs_20d",
    "drawdown_20d",
    "volatility_5d",
)
# No DOW/month features in the freeze; spy_* are the market/regime ("calendar") group.
CALENDAR_FEATURES = ("spy_return_5d", "spy_volatility_20d")

GROUPS = {
    "text": TEXT_FEATURES,
    "price": PRICE_FEATURES,
    "calendar": CALENDAR_FEATURES,
}

# Published E4 served locked-test (quote only; never re-score).
E4_PUBLISHED = {
    7: {"f1": 0.2488, "p": 0.1421, "auprc": 0.1572, "r": 1.0, "threshold": None},
    42: {"f1": 0.2460, "p": 0.1403, "auprc": 0.1648, "r": 1.0, "threshold": 0.15},
    123: {"f1": 0.2467, "p": 0.1407, "auprc": 0.2031, "r": 1.0, "threshold": None},
}
FLAG_EVERYTHING_SERVED_F1 = 0.231  # from strategy §0: 2*0.130/(1+0.130)
SERVED_BASE_RATE = 0.130


@dataclass
class FoldSpec:
    fold: int
    train_start: int
    train_end: int
    val_start: int
    val_end: int
    embargo_rows: int


def feature_mask(drop_group: str | None) -> list[str]:
    if drop_group is None:
        return list(FEATURE_NAMES)
    drop = set(GROUPS[drop_group])
    kept = [f for f in FEATURE_NAMES if f not in drop]
    if not kept:
        raise ValueError(f"drop_group={drop_group} removed all features")
    return kept


def fit_xgb(x: np.ndarray, y: np.ndarray, names: list[str], seed: int) -> xgb.Booster:
    params = {**XGB_PARAMS_BASE, "seed": seed}
    dtrain = xgb.DMatrix(x, label=y, feature_names=names)
    return xgb.train(params, dtrain, num_boost_round=NUM_BOOST_ROUND)


def predict_xgb(booster: xgb.Booster, x: np.ndarray, names: list[str]) -> np.ndarray:
    return booster.predict(xgb.DMatrix(x, feature_names=names))


def fit_logreg(x: np.ndarray, y: np.ndarray, seed: int) -> LogisticRegression:
    # Approximate scale_pos_weight=2 via class_weight.
    clf = LogisticRegression(
        max_iter=2000,
        solver="lbfgs",
        class_weight={0: 1.0, 1: 2.0},
        random_state=seed,
    )
    clf.fit(x, y)
    return clf


def calibrate(raw_train: np.ndarray, y_train: np.ndarray, raw_val: np.ndarray) -> np.ndarray:
    cal = ProbabilityCalibrator("isotonic")
    if len(np.unique(y_train)) >= 2:
        cal.fit(raw_train, y_train)
    return cal.predict_proba(raw_val)


def max_precision_at_recall(y: np.ndarray, p: np.ndarray, min_recall: float) -> dict:
    precision, recall, thresholds = precision_recall_curve(y, p)
    # sklearn returns len(thresholds)+1 points; last point is P=1,R=0 sentinel-ish.
    mask = recall >= min_recall
    if not np.any(mask):
        return {
            "max_precision": float("nan"),
            "recall_at_max_p": float("nan"),
            "threshold": float("nan"),
            "feasible": False,
        }
    idx = int(np.nanargmax(np.where(mask, precision, -np.inf)))
    thr = float(thresholds[idx]) if idx < len(thresholds) else float("nan")
    return {
        "max_precision": float(precision[idx]),
        "recall_at_max_p": float(recall[idx]),
        "threshold": thr,
        "feasible": bool(precision[idx] >= 0.20),  # decision gate uses 0.20
    }


def lift_at_k(y: np.ndarray, p: np.ndarray, ks=(0.05, 0.10, 0.20)) -> dict:
    n = len(y)
    order = np.argsort(-p)
    prev = float(y.mean()) if n else 0.0
    out = {}
    for k in ks:
        m = max(1, int(round(n * k)))
        top = y[order[:m]]
        prec = float(top.mean())
        out[f"lift@{int(k*100)}%"] = {
            "k": k,
            "n": m,
            "precision": prec,
            "lift": (prec / prev) if prev > 0 else float("nan"),
            "recall": float(top.sum() / y.sum()) if y.sum() else 0.0,
        }
    return out


def reliability_curve(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> dict:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i == n_bins - 1:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        if mask.sum() == 0:
            continue
        bins.append(
            {
                "bin": i,
                "lo": float(lo),
                "hi": float(hi),
                "n": int(mask.sum()),
                "mean_p": float(p[mask].mean()),
                "frac_pos": float(y[mask].mean()),
            }
        )
    return {"bins": bins, "brier": float(brier_score_loss(y, p))}


def f1_max_operating_point(y: np.ndarray, p: np.ndarray) -> dict:
    precision, recall, thresholds = precision_recall_curve(y, p)
    # Align thresholds with precision/recall[:-1]
    f1 = np.zeros_like(precision)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.where(
            (precision + recall) > 0,
            2 * precision * recall / (precision + recall),
            0.0,
        )
    # Exclude the final sklearn sentinel (no threshold)
    if len(thresholds) == 0:
        return {"f1": 0.0, "precision": float("nan"), "recall": float("nan"), "threshold": 0.5}
    f1_t = f1[:-1]
    idx = int(np.nanargmax(f1_t))
    return {
        "f1": float(f1_t[idx]),
        "precision": float(precision[idx]),
        "recall": float(recall[idx]),
        "threshold": float(thresholds[idx]),
    }


def flag_everything_metrics(y: np.ndarray) -> dict:
    prev = float(y.mean()) if len(y) else 0.0
    # P=prev, R=1, F1=2P/(1+P)
    f1 = (2 * prev / (1 + prev)) if prev > 0 else 0.0
    return {
        "precision": prev,
        "recall": 1.0,
        "f1": f1,
        "auprc": prev,  # random ranking expectation
        "prevalence": prev,
        "n": int(len(y)),
        "n_pos": int(y.sum()),
    }


def bootstrap_delta_auprc(
    y: np.ndarray,
    p_full: np.ndarray,
    p_ablated: np.ndarray,
    n_boot: int = 400,
    seed: int = 0,
) -> dict:
    rng = np.random.default_rng(seed)
    n = len(y)
    point = float(average_precision_score(y, p_full) - average_precision_score(y, p_ablated))
    deltas = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yi = y[idx]
        if len(np.unique(yi)) < 2:
            deltas[i] = 0.0
            continue
        deltas[i] = average_precision_score(yi, p_full[idx]) - average_precision_score(
            yi, p_ablated[idx]
        )
    lo, hi = np.quantile(deltas, [0.025, 0.975])
    return {
        "delta_auprc": point,
        "ci95_lo": float(lo),
        "ci95_hi": float(hi),
        "includes_zero": bool(lo <= 0.0 <= hi),
        "n_boot": n_boot,
    }


def build_oof_for_features(
    x_all: np.ndarray,
    y_all: np.ndarray,
    names: list[str],
    folds: list[FoldSpec],
    seed: int,
    model: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (oof_idx, oof_y, oof_p) concatenating val folds."""
    idxs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    name_idx = [list(FEATURE_NAMES).index(n) for n in names]
    for fold in folds:
        tr = slice(fold.train_start, fold.train_end)
        va = slice(fold.val_start, fold.val_end)
        x_tr = x_all[tr][:, name_idx]
        y_tr = y_all[tr]
        x_va = x_all[va][:, name_idx]
        y_va = y_all[va]
        if y_tr.sum() == 0 or y_tr.sum() == len(y_tr):
            raise RuntimeError(f"fold {fold.fold} train single-class")
        if model == "xgb":
            booster = fit_xgb(x_tr, y_tr, names, seed)
            raw_tr = predict_xgb(booster, x_tr, names)
            raw_va = predict_xgb(booster, x_va, names)
            p_va = calibrate(raw_tr, y_tr, raw_va)
        elif model == "logreg":
            clf = fit_logreg(x_tr, y_tr, seed)
            # Use predict_proba directly (already in probability space); still isotonic-calibrate.
            raw_tr = clf.predict_proba(x_tr)[:, 1]
            raw_va = clf.predict_proba(x_va)[:, 1]
            p_va = calibrate(raw_tr, y_tr, raw_va)
        else:
            raise ValueError(model)
        idxs.append(np.arange(fold.val_start, fold.val_end))
        ys.append(y_va)
        ps.append(p_va)
    return np.concatenate(idxs), np.concatenate(ys), np.concatenate(ps)


def plot_score_hist(y: np.ndarray, p: np.ndarray, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(0, 1, 41)
    ax.hist(p[y == 0], bins=bins, alpha=0.55, label="neg (y=0)", color="#4C78A8", density=True)
    ax.hist(p[y == 1], bins=bins, alpha=0.55, label="pos (y=1)", color="#F58518", density=True)
    ax.set_xlabel("calibrated score")
    ax.set_ylabel("density")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_reliability(rel: dict, path: Path, title: str) -> None:
    bins = rel["bins"]
    if not bins:
        return
    mp = [b["mean_p"] for b in bins]
    fp = [b["frac_pos"] for b in bins]
    ns = [b["n"] for b in bins]
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], "--", color="gray", label="perfect")
    ax.scatter(mp, fp, s=[max(10, n / max(ns) * 120) for n in ns], color="#E45756")
    ax.plot(mp, fp, color="#E45756", alpha=0.7)
    ax.set_xlabel("mean predicted p")
    ax.set_ylabel("empirical positive rate")
    ax.set_title(f"{title} (Brier={rel['brier']:.4f})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_pr(y: np.ndarray, p: np.ndarray, path: Path, title: str, feas: dict) -> None:
    precision, recall, _ = precision_recall_curve(y, p)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, color="#4C78A8", label="OOF PR")
    ax.axhline(y.mean(), color="gray", ls="--", label=f"prevalence={y.mean():.3f}")
    ax.axvline(0.375, color="#F58518", ls=":", label="R=0.375")
    ax.axhline(0.20, color="#E45756", ls=":", label="P=0.20 gate")
    ax.axhline(0.25, color="#54A24B", ls=":", label="P=0.25 floor")
    if not np.isnan(feas["max_precision"]):
        ax.scatter(
            [feas["recall_at_max_p"]],
            [feas["max_precision"]],
            color="black",
            zorder=5,
            label=f"maxP@R≥0.375={feas['max_precision']:.3f}",
        )
    ax.set_xlabel("recall")
    ax.set_ylabel("precision")
    ax.set_title(title)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def fp_themes(
    df: pd.DataFrame,
    oof_idx: np.ndarray,
    y: np.ndarray,
    p: np.ndarray,
    op: dict,
) -> dict:
    """FP themes at F1-max operating point on OOF."""
    thr = op["threshold"]
    pred = p >= thr
    fp_mask = (pred == 1) & (y == 0)
    tp_mask = (pred == 1) & (y == 1)
    rows = df.iloc[oof_idx].reset_index(drop=True)
    fp = rows.loc[fp_mask].copy()
    fp["score"] = p[fp_mask]

    # Ticker themes
    ticker_fp = (
        fp.groupby("ticker")
        .size()
        .sort_values(ascending=False)
        .head(15)
        .to_dict()
    )
    ticker_fp_rate = {}
    for t, c in list(ticker_fp.items())[:10]:
        n_t = int((rows["ticker"] == t).sum())
        ticker_fp_rate[t] = {"fp": int(c), "n_oof": n_t, "fp_rate": float(c / n_t) if n_t else 0.0}

    # Regime via spy_return_5d quintiles on full OOF
    spy = rows["spy_return_5d"].to_numpy(dtype=float)
    try:
        q = pd.qcut(spy, 5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"], duplicates="drop")
    except ValueError:
        q = pd.cut(spy, 5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"])
    regime = []
    q_arr = np.asarray(q, dtype=object)
    labels = [x for x in ["Q1_low", "Q2", "Q3", "Q4", "Q5_high"] if x in set(q_arr)]
    for label in labels:
        m = q_arr == label
        if m.sum() == 0:
            continue
        regime.append(
            {
                "bucket": str(label),
                "n": int(m.sum()),
                "prevalence": float(y[m].mean()),
                "fp_share": float(fp_mask[m].sum() / max(1, fp_mask.sum())),
                "fp_rate_in_bucket": float(fp_mask[m].mean()),
                "mean_score": float(p[m].mean()),
            }
        )

    # Headline clusters on FP only (lightweight)
    cluster_info: dict = {"status": "skipped", "reason": "too_few_fp"}
    if len(fp) >= 50:
        texts = fp["headline"].fillna("").astype(str).tolist()
        try:
            vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=3, stop_words="english")
            X = vec.fit_transform(texts)
            k = min(6, max(2, len(fp) // 200))
            km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=3, batch_size=1024)
            labels = km.fit_predict(X)
            terms = np.array(vec.get_feature_names_out())
            clusters = []
            for ci in range(k):
                cent = km.cluster_centers_[ci]
                top = terms[cent.argsort()[::-1][:8]].tolist()
                n_c = int((labels == ci).sum())
                # sample headlines
                sample_idx = np.flatnonzero(labels == ci)[:3]
                samples = [texts[i][:140] for i in sample_idx]
                clusters.append({"cluster": ci, "n": n_c, "top_terms": top, "samples": samples})
            cluster_info = {"status": "ok", "k": k, "clusters": clusters}
        except Exception as exc:  # noqa: BLE001
            cluster_info = {"status": "failed", "reason": str(exc)}

    return {
        "operating_point": op,
        "n_fp": int(fp_mask.sum()),
        "n_tp": int(tp_mask.sum()),
        "n_pred_pos": int(pred.sum()),
        "ticker_fp_top": {k: int(v) for k, v in ticker_fp.items()},
        "ticker_fp_rate_top": ticker_fp_rate,
        "regime_spy_return_5d": regime,
        "headline_clusters": cluster_info,
    }


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"loading {DATASET}")
    df = load_training_frame(DATASET)
    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)

    # Verify hash the same way the study executor does.
    from alphaguard.ml.train_option_b import dataset_hash

    actual_hash = dataset_hash(x_all, y_all)
    if actual_hash != EXPECTED_HASH:
        raise SystemExit(f"dataset hash mismatch: {actual_hash} != {EXPECTED_HASH}")
    print(f"dataset hash OK {actual_hash[:12]}… n={len(df)}")

    boundary = resolve_locked_test_boundary(
        df, train_frac=0.8, split_policy=SPLIT_POLICY_NESTED_V1_DATE_ANCHOR
    )
    indexed = _session_indices(df)
    assert indexed is not None
    feature_idx, label_end_idx = indexed
    next_session = int(np.min(feature_idx[boundary:]))
    train_end = prefix_end_before_session(
        label_end_idx, candidate_end=boundary, next_session=next_session
    )
    folds_raw, n_dev, embargo_src = expanding4_folds(
        len(df), train_frac=0.8, n_dev=train_end
    )
    folds_raw, purged = apply_trading_day_embargo(folds_raw, label_end_idx, feature_idx)
    folds = [
        FoldSpec(
            fold=f.fold,
            train_start=f.train_start,
            train_end=f.train_end,
            val_start=f.val_start,
            val_end=f.val_end,
            embargo_rows=f.embargo_rows,
        )
        for f in folds_raw
    ]
    print(
        f"boundary={boundary} train_end={train_end} n_dev={n_dev} "
        f"embargo_src={embargo_src} purged={purged}"
    )
    for f in folds:
        print(
            f"  fold{f.fold}: train[0:{f.train_end}) val[{f.val_start}:{f.val_end}) "
            f"embargo={f.embargo_rows}"
        )

    # Confirm locked-test never enters OOF indices.
    oof_span = max(f.val_end for f in folds)
    assert oof_span <= train_end <= boundary

    results: dict = {
        "meta": {
            "dataset": str(DATASET.relative_to(ROOT)),
            "dataset_hash": actual_hash,
            "seeds": list(SEEDS),
            "features": list(FEATURE_NAMES),
            "groups": {k: list(v) for k, v in GROUPS.items()},
            "xgb": {**XGB_PARAMS_BASE, "num_boost_round": NUM_BOOST_ROUND},
            "split": {
                "policy": SPLIT_POLICY_NESTED_V1_DATE_ANCHOR,
                "boundary": boundary,
                "train_end": train_end,
                "n_dev": n_dev,
                "embargo_source": embargo_src,
                "folds": [f.__dict__ for f in folds],
            },
            "data_rule": "OOF expanding4 purged val folds on train/dev only; locked-test not scored",
            "e4_published_quote_only": E4_PUBLISHED,
        },
        "per_seed": {},
    }

    # Aggregate containers for mean across seeds
    for seed in SEEDS:
        print(f"\n=== seed {seed} ===")
        seed_out: dict = {}

        # Full XGB OOF
        idx, y, p = build_oof_for_features(
            x_all, y_all, list(FEATURE_NAMES), folds, seed, "xgb"
        )
        print(f"  XGB OOF n={len(y)} pos={int(y.sum())} prev={y.mean():.4f}")

        flag = flag_everything_metrics(y)
        feas = max_precision_at_recall(y, p, 0.375)
        lifts = lift_at_k(y, p)
        rel = reliability_curve(y, p)
        op = f1_max_operating_point(y, p)
        auprc = float(average_precision_score(y, p))
        brier = float(brier_score_loss(y, p))

        # LogReg OOF
        idx_lr, y_lr, p_lr = build_oof_for_features(
            x_all, y_all, list(FEATURE_NAMES), folds, seed, "logreg"
        )
        assert np.array_equal(idx, idx_lr) and np.array_equal(y, y_lr)
        auprc_lr = float(average_precision_score(y_lr, p_lr))
        feas_lr = max_precision_at_recall(y_lr, p_lr, 0.375)
        op_lr = f1_max_operating_point(y_lr, p_lr)
        print(
            f"  XGB AUPRC={auprc:.4f} maxP@R≥0.375={feas['max_precision']:.4f} "
            f"F1max R={op['recall']:.3f}"
        )
        print(
            f"  LogReg AUPRC={auprc_lr:.4f} maxP@R≥0.375={feas_lr['max_precision']:.4f} "
            f"F1max R={op_lr['recall']:.3f}"
        )

        # Ablations (drop-group)
        ablations = {}
        for gname in GROUPS:
            names = feature_mask(gname)
            _, _, p_ab = build_oof_for_features(x_all, y_all, names, folds, seed, "xgb")
            a_ab = float(average_precision_score(y, p_ab))
            boot = bootstrap_delta_auprc(y, p, p_ab, n_boot=400, seed=seed + hash(gname) % 1000)
            ablations[gname] = {
                "kept_features": names,
                "dropped": list(GROUPS[gname]),
                "auprc_ablated": a_ab,
                "auprc_full": auprc,
                **boot,
            }
            print(
                f"  abl[{gname}] ΔAUPRC={boot['delta_auprc']:+.4f} "
                f"CI[{boot['ci95_lo']:+.4f},{boot['ci95_hi']:+.4f}] "
                f"incl0={boot['includes_zero']}"
            )

        # Drop-one (per feature) — point estimate + bootstrap CI
        drop_one = {}
        for feat in FEATURE_NAMES:
            names = [f for f in FEATURE_NAMES if f != feat]
            _, _, p_ab = build_oof_for_features(x_all, y_all, names, folds, seed, "xgb")
            boot = bootstrap_delta_auprc(y, p, p_ab, n_boot=200, seed=seed + hash(feat) % 1000)
            drop_one[feat] = {
                "auprc_ablated": float(average_precision_score(y, p_ab)),
                **boot,
            }
            print(f"  drop1[{feat}] Δ={boot['delta_auprc']:+.4f}")

        themes = fp_themes(df, idx, y, p, op)

        # Plots (seed 42 primary visuals; all seeds get hist)
        plot_score_hist(y, p, OUT / f"score_hist_xgb_s{seed}.png", f"OOF score hist XGB seed={seed}")
        if seed == 42:
            plot_reliability(rel, OUT / "reliability_xgb_s42.png", "OOF reliability XGB s42")
            plot_pr(y, p, OUT / "pr_curve_xgb_s42.png", "OOF PR XGB s42", feas)
            plot_score_hist(y, p_lr, OUT / "score_hist_logreg_s42.png", "OOF score hist LogReg s42")

        seed_out = {
            "n_oof": int(len(y)),
            "n_pos": int(y.sum()),
            "prevalence": float(y.mean()),
            "flag_everything": flag,
            "xgb": {
                "auprc": auprc,
                "brier": brier,
                "feasibility_max_p_at_r_ge_0_375": feas,
                "lift_at_k": lifts,
                "reliability": rel,
                "f1_max_op": op,
                "lift_over_flag_f1": float(op["f1"] / flag["f1"]) if flag["f1"] else float("nan"),
                "lift_auprc_over_prev": float(auprc / y.mean()) if y.mean() else float("nan"),
            },
            "logreg": {
                "auprc": auprc_lr,
                "brier": float(brier_score_loss(y, p_lr)),
                "feasibility_max_p_at_r_ge_0_375": feas_lr,
                "f1_max_op": op_lr,
                "lift_at_k": lift_at_k(y, p_lr),
            },
            "ablation_groups": ablations,
            "ablation_drop_one": drop_one,
            "fp_themes": themes,
            "oof_idx_hash": int(idx.sum()),  # cheap integrity marker
        }
        results["per_seed"][str(seed)] = seed_out

        # Persist OOF scores for seed 42 (audit)
        if seed == 42:
            np.savez_compressed(
                OUT / "oof_scores_s42.npz",
                idx=idx,
                y=y,
                p_xgb=p,
                p_logreg=p_lr,
            )

    # Cross-seed summary
    def _mean(key_path):
        vals = []
        for s in SEEDS:
            d = results["per_seed"][str(s)]
            cur = d
            for k in key_path:
                cur = cur[k]
            vals.append(float(cur))
        return float(np.mean(vals)), float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

    feas_ps = [
        results["per_seed"][str(s)]["xgb"]["feasibility_max_p_at_r_ge_0_375"]["max_precision"]
        for s in SEEDS
    ]
    text_incl0 = [
        results["per_seed"][str(s)]["ablation_groups"]["text"]["includes_zero"] for s in SEEDS
    ]
    text_deltas = [
        results["per_seed"][str(s)]["ablation_groups"]["text"]["delta_auprc"] for s in SEEDS
    ]
    text_los = [
        results["per_seed"][str(s)]["ablation_groups"]["text"]["ci95_lo"] for s in SEEDS
    ]
    text_his = [
        results["per_seed"][str(s)]["ablation_groups"]["text"]["ci95_hi"] for s in SEEDS
    ]
    f1max_recalls = [
        results["per_seed"][str(s)]["xgb"]["f1_max_op"]["recall"] for s in SEEDS
    ]

    mean_feas_p = float(np.mean(feas_ps))
    decision_i = mean_feas_p < 0.20  # infeasible
    # (ii) feasible region exists but picker chose R≈1 — use E4 published R=1 + OOF F1-max R
    any_feas = any(p >= 0.20 for p in feas_ps)
    picker_r_approx_1 = all(
        (E4_PUBLISHED[s].get("r") or 0) >= 0.95 for s in SEEDS
    ) or all(r >= 0.90 for r in f1max_recalls)
    decision_ii = (not decision_i) and picker_r_approx_1
    # Also note selection-rule defect evidence even if infeasible: E4 R=1
    selection_rule_defect_evidence = picker_r_approx_1

    # (iii) text ΔAUPRC CI includes 0 — require majority of seeds
    decision_iii = sum(1 for x in text_incl0 if x) >= 2

    results["aggregate"] = {
        "flag_everything_oof_f1_mean": _mean(("flag_everything", "f1")),
        "xgb_oof_auprc_mean": _mean(("xgb", "auprc")),
        "xgb_oof_brier_mean": _mean(("xgb", "brier")),
        "logreg_oof_auprc_mean": _mean(("logreg", "auprc")),
        "feasibility_max_p_at_r_ge_0_375": {
            "per_seed": {str(s): feas_ps[i] for i, s in enumerate(SEEDS)},
            "mean": mean_feas_p,
            "std": float(np.std(feas_ps, ddof=1)),
        },
        "xgb_f1max_recall_per_seed": {str(s): f1max_recalls[i] for i, s in enumerate(SEEDS)},
        "text_ablation": {
            "delta_per_seed": {str(s): text_deltas[i] for i, s in enumerate(SEEDS)},
            "ci_includes_zero_per_seed": {str(s): text_incl0[i] for i, s in enumerate(SEEDS)},
            "mean_delta": float(np.mean(text_deltas)),
            "mean_ci_lo": float(np.mean(text_los)),
            "mean_ci_hi": float(np.mean(text_his)),
        },
        "wall_time_s": time.time() - t0,
    }
    results["decision"] = {
        "i_infeasible_claim": {
            "rule": "OOF feasibility max P at R≥0.375 < 0.20 → claim infeasible with this feature set → Bet 2",
            "mean_max_p": mean_feas_p,
            "threshold": 0.20,
            "triggered": decision_i,
            "next": "Bet 2" if decision_i else "not triggered",
        },
        "ii_selection_rule_defect": {
            "rule": "Feasible region exists on OOF but picker chose R≈1 → selection-rule defect → fresh holdout + fixed rule",
            "any_seed_feasible_p_ge_0_20": any_feas,
            "infeasible_by_i": decision_i,
            "picker_r_approx_1_evidence": selection_rule_defect_evidence,
            "e4_served_recall_published": {str(s): E4_PUBLISHED[s]["r"] for s in SEEDS},
            "oof_f1max_recall": {str(s): f1max_recalls[i] for i, s in enumerate(SEEDS)},
            "triggered": decision_ii,
            "note": (
                "E4 served locked-test recall=1.0 at chosen threshold for all seeds "
                "(published; not re-scored). OOF F1-max recall also listed."
            ),
            "next": "pre-register fixed rule + fresh holdout" if decision_ii else "not triggered (or subsumed by i)",
        },
        "iii_text_ci_includes_zero": {
            "rule": "text-group ΔAUPRC CI includes 0 → Bet 3 eligible",
            "per_seed_includes_zero": {str(s): text_incl0[i] for i, s in enumerate(SEEDS)},
            "majority_includes_zero": decision_iii,
            "triggered": decision_iii,
            "next": "Bet 3 eligible" if decision_iii else "Bet 3 not eligible on this evidence",
        },
        "primary_next_step": (
            "Bet 2 (new claim / fresh holdout)"
            if decision_i
            else (
                "selection-rule fix on fresh holdout"
                if decision_ii
                else "revisit diagnosis"
            )
        ),
    }

    out_json = OUT / "diagnosis.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {out_json} in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
