"""JH-63.1 — binary Fβ threshold math (no parquet, no held-out test)."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import fbeta_score

from alphaguard.ml.train_eval import (
    THRESHOLD_GRID,
    classification_counts,
    fbeta_from_counts,
    fit_threshold_train_f1,
    fit_threshold_train_val_fbeta,
    train_val_sizes,
)
from alphaguard.ml.train_option_b_errors import TrainError


def test_fbeta_matches_sklearn_binary_definition() -> None:
    y = np.array([1, 0, 1, 0, 1, 0, 0, 0])
    pred = np.array([1, 1, 0, 0, 1, 0, 0, 1])
    counts = classification_counts(y, pred)
    got = fbeta_from_counts(counts, beta=0.5)
    binary = fbeta_score(y, pred, beta=0.5, average="binary", zero_division=0)
    weighted = fbeta_score(y, pred, beta=0.5, average="weighted", zero_division=0)
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    beta2 = 0.25
    expected = (1 + beta2) * tp / ((1 + beta2) * tp + fp + beta2 * fn)
    assert got == pytest.approx(expected)
    assert got == pytest.approx(float(binary))
    assert got != pytest.approx(float(weighted))


def test_fbeta_zero_when_denominator_empty() -> None:
    assert fbeta_from_counts({"tp": 0, "fp": 0, "tn": 4, "fn": 0}, beta=0.5) == 0.0


def test_train_val_sizes_last_fifth_of_train() -> None:
    assert train_val_sizes(400) == (320, 80)
    assert train_val_sizes(128) == (102, 26)


def test_fbeta_tie_break_higher_precision_then_lower_t() -> None:
    # t<=0.40 → TP=2 FP=1 FN=2 (Fβ=0.625, P≈0.667)
    # t in [0.45, 0.90] → TP=1 FP=0 FN=3 (Fβ=0.625, P=1)
    # Equal Fβ: higher precision wins, then the lower t in that plateau (0.45).
    y = np.array([1, 1, 0, 1, 1])
    probs = np.array([0.90, 0.40, 0.40, 0.02, 0.02])
    assert fit_threshold_train_val_fbeta(y, probs) == pytest.approx(0.45)


def test_fbeta_tie_break_lower_t_when_precision_matches() -> None:
    # t in [0.15, 0.80] shares TP=1 FP=0 (Fβ=1). Lowest such grid point wins.
    y = np.array([1, 0])
    probs = np.array([0.80, 0.10])
    assert fit_threshold_train_val_fbeta(y, probs) == pytest.approx(0.15)


def test_fbeta_grid_matches_train_f1_grid() -> None:
    assert len(THRESHOLD_GRID) == 19
    assert THRESHOLD_GRID[0] == pytest.approx(0.05)
    assert THRESHOLD_GRID[-1] == pytest.approx(0.95)


def test_single_class_val_refuses_fbeta_fit() -> None:
    y = np.array([0, 0, 0, 0])
    probs = np.array([0.2, 0.4, 0.6, 0.8])
    with pytest.raises(TrainError, match="<2 classes"):
        fit_threshold_train_val_fbeta(y, probs)


def test_train_f1_path_still_available() -> None:
    y = np.array([0, 0, 1, 1, 0, 1, 0, 1], dtype=int)
    probs = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.15, 0.85])
    t = fit_threshold_train_f1(y, probs)
    assert 0.05 <= t <= 0.95
