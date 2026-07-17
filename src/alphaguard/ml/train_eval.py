"""Train-time classification metrics + threshold fit (Guide 05b)."""

from __future__ import annotations

import numpy as np

from alphaguard.ml.train_option_b_errors import TrainError


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


def fit_threshold_train_f1(y_true: np.ndarray, probs: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        raise TrainError("cannot fit threshold: train labels have <2 classes")
    best_t, best_f1 = None, -1.0
    for t in np.linspace(0.05, 0.95, 19):
        pred = (probs >= t).astype(int)
        _, _, f1 = prf1(classification_counts(y_true, pred))
        if f1 > best_f1 or (f1 == best_f1 and (best_t is None or t < best_t)):
            best_f1, best_t = f1, float(t)
    if best_t is None or best_f1 < 0:
        raise TrainError("F1 undefined across threshold grid — fail closed")
    return best_t


def split_metrics(y_true: np.ndarray, probs: np.ndarray, threshold: float) -> dict:
    pred = (probs >= threshold).astype(int)
    counts = classification_counts(y_true, pred)
    precision, recall, f1 = prf1(counts)
    return {"precision": precision, "recall": recall, "f1": f1, **counts}
