"""Train-time classification metrics + threshold fit (Guide 05b / JH-63.1)."""

from __future__ import annotations

import numpy as np

from alphaguard.ml.train_option_b_errors import TrainError

THRESHOLD_TRAIN_F1 = "train_f1_max"
THRESHOLD_TRAIN_VAL_FBETA = "train_val_fbeta_0.5"
THRESHOLD_GRID = np.linspace(0.05, 0.95, 19)
DEFAULT_VAL_FRAC = 0.2
DEFAULT_FBETA = 0.5


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


def fbeta(precision: float, recall: float, beta: float = DEFAULT_FBETA) -> float:
    if precision + recall == 0:
        return 0.0
    b2 = beta * beta
    return (1.0 + b2) * precision * recall / (b2 * precision + recall)


def train_val_slices(n: int, val_frac: float = DEFAULT_VAL_FRAC) -> tuple[slice, slice]:
    """Time-ordered fit / val slices (caller must already sort by time)."""
    if n < 2:
        raise TrainError(f"train-val split too small: n={n}")
    n_fit = int(n * (1.0 - val_frac))
    if n_fit < 1 or n_fit >= n:
        raise TrainError(f"train-val split empty: n={n}, n_fit={n_fit}")
    return slice(0, n_fit), slice(n_fit, n)


def fit_threshold_train_f1(y_true: np.ndarray, probs: np.ndarray) -> float:
    if len(y_true) != len(probs):
        raise TrainError("cannot fit threshold: y_true/probs length mismatch")
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
    y_true: np.ndarray,
    probs: np.ndarray,
    *,
    beta: float = DEFAULT_FBETA,
    val_frac: float = DEFAULT_VAL_FRAC,
) -> float:
    """Maximize Fβ on the last `val_frac` of a time-ordered train array.

    Never inspects rows outside that val slice (test must not be passed in).
    Tie-break: higher precision, then lower threshold.
    """
    if len(y_true) != len(probs):
        raise TrainError("cannot fit val Fbeta: y_true/probs length mismatch")
    _, val = train_val_slices(len(y_true), val_frac)
    y_val, p_val = y_true[val], probs[val]
    if len(np.unique(y_val)) < 2:
        raise TrainError("cannot fit val Fbeta: val labels have <2 classes")
    best_t: float | None = None
    best_fb = -1.0
    best_prec = -1.0
    for t in THRESHOLD_GRID:
        pred = (p_val >= t).astype(int)
        precision, recall, _ = prf1(classification_counts(y_val, pred))
        fb = fbeta(precision, recall, beta)
        better = fb > best_fb
        if fb == best_fb and precision > best_prec:
            better = True
        if fb == best_fb and precision == best_prec and (best_t is None or float(t) < best_t):
            better = True
        if better:
            best_fb, best_prec, best_t = fb, precision, float(t)
    if best_t is None:
        raise TrainError("Fbeta undefined across threshold grid — fail closed")
    return best_t


def resolve_threshold(
    method: str,
    y_train: np.ndarray,
    train_probs: np.ndarray,
) -> tuple[float, str, str | None]:
    """Return (threshold, method_used, fallback_reason)."""
    if method == THRESHOLD_TRAIN_F1:
        return fit_threshold_train_f1(y_train, train_probs), THRESHOLD_TRAIN_F1, None
    if method == THRESHOLD_TRAIN_VAL_FBETA:
        try:
            t = fit_threshold_train_val_fbeta(y_train, train_probs)
            return t, THRESHOLD_TRAIN_VAL_FBETA, None
        except TrainError as exc:
            t = fit_threshold_train_f1(y_train, train_probs)
            return t, THRESHOLD_TRAIN_F1, str(exc)
    raise TrainError(f"unknown threshold_fitting: {method}")


def split_metrics(y_true: np.ndarray, probs: np.ndarray, threshold: float) -> dict:
    pred = (probs >= threshold).astype(int)
    counts = classification_counts(y_true, pred)
    precision, recall, f1 = prf1(counts)
    return {"precision": precision, "recall": recall, "f1": f1, **counts}
