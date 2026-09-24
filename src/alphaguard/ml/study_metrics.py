"""Evaluation metrics suite for rare events (JH-63.2).

Computes Precision, Recall, F1, Fβ, AUPRC, Brier score, prevalence,
and confusion matrix counts.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss

from alphaguard.ml.train_eval import (
    FBETA_BETA,
    classification_counts,
    fbeta_from_counts,
    prf1,
)


def compute_metrics_suite(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float,
    beta: float = FBETA_BETA,
) -> dict[str, Any]:
    """Compute comprehensive classification and probability metrics for a binary split."""
    y_arr = np.asarray(y_true, dtype=int)
    p_arr = np.asarray(probs, dtype=float)
    n_total = len(y_arr)
    n_pos = int(y_arr.sum())
    prevalence = float(n_pos / n_total) if n_total > 0 else 0.0

    preds = (p_arr >= threshold).astype(int)
    counts = classification_counts(y_arr, preds)
    precision, recall, f1 = prf1(counts)
    fbeta = fbeta_from_counts(counts, beta=beta)

    # AUPRC (average precision score). Handled gracefully if only 1 class is present.
    unique_classes = np.unique(y_arr)
    if len(unique_classes) >= 2:
        auprc = float(average_precision_score(y_arr, p_arr))
        brier = float(brier_score_loss(y_arr, p_arr))
    else:
        # Undefined / degenerate case when single class
        auprc = float(prevalence)
        brier = float(np.mean((p_arr - y_arr) ** 2)) if n_total > 0 else 0.0

    return {
        "n_samples": n_total,
        "n_positive": n_pos,
        "prevalence": prevalence,
        "threshold": float(threshold),
        "beta": float(beta),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "fbeta": float(fbeta),
        "auprc": auprc,
        "brier": brier,
        "confusion": counts,
    }
