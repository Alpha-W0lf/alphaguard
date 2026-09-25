"""Expanding-window walk-forward inside the dev block only (Phase B).

Layout: first 40% of dev is the initial train, then four contiguous validation
blocks of 15% of dev. Fold k trains on everything before val block k, minus
an embargo gap. The locked test (last 20%) is not indexed here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_calibration import ProbabilityCalibrator
from alphaguard.ml.study_metrics import compute_metrics_suite
from alphaguard.ml.study_schema import (
    RunConfig,
    WalkForwardAggregate,
    WalkForwardBlock,
    WalkForwardFoldMetrics,
)
from alphaguard.ml.train_eval import fit_threshold_train_f1

logger = logging.getLogger(__name__)

# Label window end is close_5_trading_sessions_later (fwd_return_5d).
LABEL_HORIZON_ROWS = 5
_AGG_KEYS = ("f1", "precision", "recall", "auprc", "positive_rate")


@dataclass(frozen=True)
class FoldIndex:
    fold: int
    train_start: int
    train_end: int
    val_start: int
    val_end: int
    embargo_rows: int


@dataclass
class FoldScore:
    """Val-block scores for the economic stub. Threshold was fit on train only."""

    index: FoldIndex
    y_val: np.ndarray
    probs_val: np.ndarray
    threshold: float
    metrics: WalkForwardFoldMetrics


def resolve_embargo_rows(
    n_dev: int,
    explicit: int | None,
    horizon_rows: int | None = LABEL_HORIZON_ROWS,
) -> tuple[int, str]:
    """Default embargo equals the label horizon. Else 1% of dev rows."""
    if explicit is not None:
        if explicit < 0:
            raise ValueError(f"embargo_rows must be >= 0, got {explicit}")
        return explicit, "explicit"
    if horizon_rows is not None:
        if horizon_rows < 0:
            raise ValueError(f"label horizon must be >= 0, got {horizon_rows}")
        return horizon_rows, "label_horizon"
    return int(n_dev * 0.01), "dev_rows_1pct"


def expanding4_folds(
    n_rows: int,
    *,
    train_frac: float = 0.8,
    n_dev: int | None = None,
    embargo_rows: int | None = None,
    horizon_rows: int | None = LABEL_HORIZON_ROWS,
) -> tuple[list[FoldIndex], int, str]:
    """Return 4 purged expanding folds and the locked-test start index.

    Val blocks are contiguous slices of dev. Train for fold k is the prefix
    that ends `embargo_rows` before that val block. Locked-test rows start at n_dev.
    """
    if n_dev is None:
        n_dev = int(n_rows * train_frac)
    if n_dev < 1 or n_dev >= n_rows:
        raise ValueError(f"dev block must be a proper prefix: n_dev={n_dev} n_rows={n_rows}")
    embargo, source = resolve_embargo_rows(n_dev, embargo_rows, horizon_rows)
    logger.info(
        "walk-forward embargo_rows=%s source=%s n_dev=%s n_rows=%s",
        embargo,
        source,
        n_dev,
        n_rows,
    )
    fracs = (0.40, 0.55, 0.70, 0.85, 1.0)
    cuts = [int(n_dev * frac) for frac in fracs]
    cuts[-1] = n_dev
    for i in range(1, len(cuts)):
        if cuts[i] <= cuts[i - 1]:
            raise ValueError(f"dev block too small for expanding4 cuts: {cuts}")

    folds: list[FoldIndex] = []
    for k in range(4):
        val_start, val_end = cuts[k], cuts[k + 1]
        train_end = val_start - embargo
        if train_end < 1:
            raise ValueError(
                f"fold {k} train empty after embargo={embargo} (val_start={val_start})"
            )
        if val_end > n_dev:
            raise ValueError(f"fold {k} val crosses locked test: val_end={val_end} n_dev={n_dev}")
        folds.append(
            FoldIndex(
                fold=k,
                train_start=0,
                train_end=train_end,
                val_start=val_start,
                val_end=val_end,
                embargo_rows=embargo,
            )
        )
    return folds, n_dev, source


def _aggregate(folds: list[WalkForwardFoldMetrics]) -> WalkForwardAggregate:
    mean: dict[str, float] = {}
    minimum: dict[str, float] = {}
    std: dict[str, float] = {}
    for key in _AGG_KEYS:
        vals = np.asarray([float(getattr(fold, key)) for fold in folds], dtype=float)
        mean[key] = float(vals.mean())
        minimum[key] = float(vals.min())
        std[key] = float(vals.std(ddof=1)) if len(vals) >= 2 else 0.0
    return WalkForwardAggregate(mean=mean, min=minimum, std=std)


def _fit_fold_calibrator(
    method: str, train_probs: np.ndarray, y_train: np.ndarray
) -> ProbabilityCalibrator:
    """Fit calibration on this fold's train rows only. Never on val or test."""
    calibrator = ProbabilityCalibrator(method)  # type: ignore[arg-type]
    if method != "none" and len(np.unique(y_train)) >= 2:
        calibrator.fit(train_probs, y_train)
    return calibrator


def evaluate_expanding4(
    df: pd.DataFrame,
    config: RunConfig,
    *,
    n_dev: int,
    embargo_rows: int | None = None,
) -> tuple[WalkForwardBlock, list[FoldScore]]:
    """Train one booster per fold. Threshold is train_f1_max on that fold's train."""
    from alphaguard.ml.study_executor import _build_booster_params

    folds, locked_start, source = expanding4_folds(
        len(df),
        train_frac=config.train_frac,
        n_dev=n_dev,
        embargo_rows=embargo_rows,
    )
    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    scored: list[FoldScore] = []
    metrics: list[WalkForwardFoldMetrics] = []

    for fold in folds:
        y_tr = y_all[fold.train_start : fold.train_end]
        x_tr = x_all[fold.train_start : fold.train_end]
        n_pos = int(y_tr.sum())
        if n_pos == 0 or n_pos == len(y_tr):
            raise ValueError(f"fold {fold.fold} train is single-class (n_pos={n_pos})")
        spw = float(len(y_tr) - n_pos) / float(n_pos)
        params = _build_booster_params(config, spw)
        dtrain = xgb.DMatrix(x_tr, label=y_tr, feature_names=list(FEATURE_NAMES))
        booster = xgb.train(
            params, dtrain, num_boost_round=config.model_params.num_boost_round
        )
        raw_train = booster.predict(dtrain)
        calibrator = _fit_fold_calibrator(config.calibration_method, raw_train, y_tr)
        train_probs = calibrator.predict_proba(raw_train)
        threshold = fit_threshold_train_f1(y_tr, train_probs)

        y_va = y_all[fold.val_start : fold.val_end]
        x_va = x_all[fold.val_start : fold.val_end]
        dval = xgb.DMatrix(x_va, feature_names=list(FEATURE_NAMES))
        val_probs = calibrator.predict_proba(booster.predict(dval))
        suite = compute_metrics_suite(y_va, val_probs, threshold=threshold, beta=config.beta)
        n_rows = int(len(y_va))
        positive_rate = float(y_va.sum() / n_rows) if n_rows else 0.0
        logger.info(
            "walk-forward fold=%s n_rows=%s positive_rate=%.6f",
            fold.fold,
            n_rows,
            positive_rate,
        )
        fold_metrics = WalkForwardFoldMetrics(
            fold=fold.fold,
            n_rows=n_rows,
            positive_rate=positive_rate,
            precision=float(suite["precision"]),
            recall=float(suite["recall"]),
            f1=float(suite["f1"]),
            auprc=float(suite["auprc"]),
            threshold=float(threshold),
            train_start=fold.train_start,
            train_end=fold.train_end,
            val_start=fold.val_start,
            val_end=fold.val_end,
        )
        metrics.append(fold_metrics)
        scored.append(
            FoldScore(
                index=fold,
                y_val=y_va,
                probs_val=val_probs,
                threshold=float(threshold),
                metrics=fold_metrics,
            )
        )

    block = WalkForwardBlock(
        embargo_rows=folds[0].embargo_rows,
        embargo_source=source,
        n_dev=locked_start,
        locked_test_start=locked_start,
        folds=metrics,
        aggregate=_aggregate(metrics),
    )
    return block, scored
