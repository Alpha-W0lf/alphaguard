"""Calibration methods for probability outputs.

Supports 'none', 'platt' (logistic regression), and 'isotonic'.
Calibration models must be fit on train/val ONLY, never on test rows.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

CalibrationMethod = Literal["none", "platt", "isotonic"]
CALIBRATION_METHODS: tuple[CalibrationMethod, ...] = ("none", "platt", "isotonic")


def _logit(probs: np.ndarray) -> np.ndarray:
    p = np.asarray(probs, dtype=float).clip(1e-7, 1.0 - 1e-7)
    return np.log(p / (1.0 - p))


def apply_platt(probs: np.ndarray, coef: float, intercept: float) -> np.ndarray:
    """Platt map sigmoid(coef * logit(p) + intercept). Same as the fitted LogisticRegression."""
    return 1.0 / (1.0 + np.exp(-(coef * _logit(probs) + intercept)))


def reliability_summary(
    y_true: np.ndarray, probs: np.ndarray, n_bins: int = 10
) -> dict[str, Any]:
    """Brier score, expected calibration error and equal-width reliability bins."""
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probs, dtype=float)
    idx = np.minimum((p * n_bins).astype(int), n_bins - 1)
    bins: list[dict[str, float | int]] = []
    ece = 0.0
    for b in range(n_bins):
        mask = idx == b
        n = int(mask.sum())
        if n == 0:
            continue
        mean_pred = float(p[mask].mean())
        frac_pos = float(y[mask].mean())
        ece += n / len(p) * abs(mean_pred - frac_pos)
        bins.append(
            {
                "lo": b / n_bins,
                "hi": (b + 1) / n_bins,
                "n": n,
                "mean_pred": mean_pred,
                "frac_pos": frac_pos,
            }
        )
    return {
        "n": int(len(p)),
        "prevalence": float(y.mean()) if len(y) else 0.0,
        "mean_pred": float(p.mean()) if len(p) else 0.0,
        "brier": float(brier_score_loss(y, p)),
        "ece": float(ece),
        "bins": bins,
    }


class ProbabilityCalibrator:
    """Wraps optional Platt or Isotonic calibration, fit on train or validation probabilities."""

    def __init__(self, method: CalibrationMethod = "none") -> None:
        if method not in CALIBRATION_METHODS:
            raise ValueError(
                f"Unknown calibration method: {method!r}. Expected {CALIBRATION_METHODS}"
            )
        self.method: CalibrationMethod = method
        self._model: LogisticRegression | IsotonicRegression | None = None

    def fit(self, probs: np.ndarray, y_true: np.ndarray) -> ProbabilityCalibrator:
        if self.method == "none":
            return self

        p = np.asarray(probs, dtype=float).clip(1e-7, 1.0 - 1e-7)
        y = np.asarray(y_true, dtype=int)

        if len(np.unique(y)) < 2:
            # Cannot calibrate with single class; keep uncalibrated
            self.method = "none"
            return self

        if self.method == "platt":
            # Platt scaling: logistic regression on logit(p)
            clf = LogisticRegression(C=1.0, solver="lbfgs")
            clf.fit(_logit(p).reshape(-1, 1), y)
            self._model = clf
        elif self.method == "isotonic":
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(p, y)
            self._model = iso

        return self

    def predict_proba(self, probs: np.ndarray) -> np.ndarray:
        if self.method == "none" or self._model is None:
            return np.asarray(probs, dtype=float)

        p = np.asarray(probs, dtype=float).clip(1e-7, 1.0 - 1e-7)
        if self.method == "platt":
            coef, intercept = self.platt_params()
            return apply_platt(p, coef, intercept)
        elif self.method == "isotonic":
            return np.asarray(self._model.predict(p), dtype=float)

        return p

    def platt_params(self) -> tuple[float, float]:
        """(coef, intercept) of a fitted Platt calibrator, for the bundle manifest."""
        if self.method != "platt" or not isinstance(self._model, LogisticRegression):
            raise ValueError("platt_params needs a fitted 'platt' calibrator")
        return float(self._model.coef_[0][0]), float(self._model.intercept_[0])
