"""Train-time classification metrics + threshold fit (Guide 05b, JH-63.1)."""

from __future__ import annotations

import numpy as np

from alphaguard.ml.train_option_b_errors import TrainError

METHOD_TRAIN_F1_MAX = "train_f1_max"
METHOD_TRAIN_VAL_FBETA = "train_val_fbeta_0.5"
THRESHOLD_METHODS = (METHOD_TRAIN_F1_MAX, METHOD_TRAIN_VAL_FBETA)
FBETA_BETA = 0.5
TRAIN_VAL_FRACTION = 0.2
VAL_SINGLE_CLASS_REASON = "val labels have <2 classes"
# 0.05, 0.10, ..., 0.95 — same grid for train-F1 and train-val Fβ.
THRESHOLD_GRID = np.linspace(0.05, 0.95, 19)


def classification_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def prf1(counts: dict[str, int]) -> tuple[float, float, float]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def fbeta_from_counts(counts: dict[str, int], beta: float = FBETA_BETA) -> float:
    """Binary positive-class Fβ.

    Sklearn definition: (1+β²) TP / ((1+β²) TP + FP + β² FN).
    This is not a multilabel average='weighted' score.
    """
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    beta2 = beta * beta
    denom = (1.0 + beta2) * tp + fp + beta2 * fn
    if denom == 0.0:
        return 0.0
    return (1.0 + beta2) * tp / denom


def train_val_sizes(n_train: int, val_frac: float = TRAIN_VAL_FRACTION) -> tuple[int, int]:
    """Time-ordered train split: fit is the prefix, val is the last `val_frac`."""
    if not 0.0 < val_frac < 1.0:
        raise TrainError(f"val_frac must be in (0, 1), got {val_frac}")
    n_fit = int(n_train * (1.0 - val_frac))
    n_val = n_train - n_fit
    if n_fit < 1 or n_val < 1:
        raise TrainError(f"train too small for fit/val threshold split: n_train={n_train}")
    return n_fit, n_val


def _prefer_fbeta_candidate(
    fbeta: float,
    precision: float,
    t: float,
    best_fbeta: float,
    best_precision: float,
    best_t: float | None,
) -> bool:
    """Maximize Fβ, then precision, then the lower threshold."""
    if best_t is None or fbeta > best_fbeta:
        return True
    if fbeta < best_fbeta:
        return False
    if precision > best_precision:
        return True
    if precision < best_precision:
        return False
    return t < best_t


def fit_threshold_train_f1(y_true: np.ndarray, probs: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        raise TrainError("cannot fit threshold: train labels have <2 classes")
    best_t, best_f1 = None, -1.0
    for t in THRESHOLD_GRID:
        pred = (probs >= t).astype(int)
        _, _, f1 = prf1(classification_counts(y_true, pred))
        if f1 > best_f1 or (f1 == best_f1 and (best_t is None or t < best_t)):
            best_f1, best_t = f1, float(t)
    if best_t is None or best_f1 < 0:
        raise TrainError("F1 undefined across threshold grid — fail closed")
    return best_t


def fit_threshold_train_val_fbeta(
    y_val: np.ndarray,
    probs_val: np.ndarray,
    *,
    beta: float = FBETA_BETA,
) -> float:
    """Pick t on train-internal val only. Caller must not pass test rows."""
    if len(y_val) != len(probs_val):
        raise TrainError("y_val/probs_val length mismatch")
    if len(np.unique(y_val)) < 2:
        raise TrainError(f"cannot fit threshold: {VAL_SINGLE_CLASS_REASON}")
    best_t: float | None = None
    best_fbeta = -1.0
    best_precision = -1.0
    for t in THRESHOLD_GRID:
        pred = (probs_val >= t).astype(int)
        counts = classification_counts(y_val, pred)
        fbeta = fbeta_from_counts(counts, beta=beta)
        precision, _, _ = prf1(counts)
        t_f = float(t)
        if _prefer_fbeta_candidate(fbeta, precision, t_f, best_fbeta, best_precision, best_t):
            best_fbeta, best_precision, best_t = fbeta, precision, t_f
    if best_t is None:
        raise TrainError("Fβ undefined across threshold grid — fail closed")
    return best_t


def split_metrics(y_true: np.ndarray, probs: np.ndarray, threshold: float) -> dict:
    pred = (probs >= threshold).astype(int)
    counts = classification_counts(y_true, pred)
    precision, recall, f1 = prf1(counts)
    return {"precision": precision, "recall": recall, "f1": f1, **counts}
