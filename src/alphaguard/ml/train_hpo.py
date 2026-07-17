"""Nested time-aware HPO for Option B XGBoost (Guide 05b)."""

from __future__ import annotations

from typing import Any

import numpy as np
import xgboost as xgb
from sklearn.metrics import log_loss
from sklearn.model_selection import TimeSeriesSplit

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.train_option_b_errors import TrainError

HPO_DEPTH = (2, 3)
HPO_ETA = (0.05, 0.1)
HPO_ROUNDS = (40, 60)
N_SPLITS = 3
MIN_FOLD_ROWS = 10

FIXED_PARAMS: dict[str, Any] = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "seed": 42,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
}


def booster_params(scale_pos_weight: float, max_depth: int, eta: float) -> dict[str, Any]:
    return {
        **FIXED_PARAMS,
        "max_depth": max_depth,
        "eta": eta,
        "scale_pos_weight": scale_pos_weight,
    }


def train_booster(
    x: np.ndarray,
    y: np.ndarray,
    *,
    max_depth: int,
    eta: float,
    num_boost_round: int,
    scale_pos_weight: float,
) -> xgb.Booster:
    dtrain = xgb.DMatrix(x, label=y, feature_names=list(FEATURE_NAMES))
    return xgb.train(
        booster_params(scale_pos_weight, max_depth, eta),
        dtrain,
        num_boost_round=num_boost_round,
    )


def _is_better(cand: dict[str, Any], best: dict[str, Any]) -> bool:
    if cand["fold_mean_logloss"] < best["fold_mean_logloss"]:
        return True
    if cand["fold_mean_logloss"] > best["fold_mean_logloss"]:
        return False
    for key in ("max_depth", "eta", "num_boost_round"):
        if cand[key] < best[key]:
            return True
        if cand[key] > best[key]:
            return False
    return False


def run_hpo(
    x_train: np.ndarray,
    y_train: np.ndarray,
    scale_pos_weight: float,
) -> dict[str, Any]:
    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    space = {
        "max_depth": list(HPO_DEPTH),
        "eta": list(HPO_ETA),
        "num_boost_round": list(HPO_ROUNDS),
    }
    best: dict[str, Any] | None = None
    candidates = 0
    for max_depth in HPO_DEPTH:
        for eta in HPO_ETA:
            for num_boost_round in HPO_ROUNDS:
                candidates += 1
                fold_losses: list[float] = []
                for tr_idx, va_idx in tscv.split(x_train):
                    if len(va_idx) < MIN_FOLD_ROWS:
                        raise TrainError(
                            f"HPO fold too small: val_rows={len(va_idx)} < {MIN_FOLD_ROWS}"
                        )
                    y_tr, y_va = y_train[tr_idx], y_train[va_idx]
                    if len(np.unique(y_tr)) < 2 or len(np.unique(y_va)) < 2:
                        raise TrainError("HPO fold has <2 classes — fail closed")
                    booster = train_booster(
                        x_train[tr_idx],
                        y_tr,
                        max_depth=max_depth,
                        eta=eta,
                        num_boost_round=num_boost_round,
                        scale_pos_weight=scale_pos_weight,
                    )
                    dval = xgb.DMatrix(x_train[va_idx], feature_names=list(FEATURE_NAMES))
                    probs = booster.predict(dval)
                    fold_losses.append(float(log_loss(y_va, probs, labels=[0, 1])))
                mean_ll = float(np.mean(fold_losses))
                cand = {
                    "max_depth": max_depth,
                    "eta": eta,
                    "num_boost_round": num_boost_round,
                    "fold_logloss": fold_losses,
                    "fold_mean_logloss": mean_ll,
                }
                if best is None or _is_better(cand, best):
                    best = cand
    assert best is not None
    return {
        "method": "timeseries_split_grid",
        "n_splits": N_SPLITS,
        "space": space,
        "selection": "mean_val_logloss",
        "candidates_evaluated": candidates,
        "winner": {
            "max_depth": best["max_depth"],
            "eta": best["eta"],
            "num_boost_round": best["num_boost_round"],
        },
        "fold_logloss": best["fold_logloss"],
        "fold_mean_logloss": best["fold_mean_logloss"],
    }
