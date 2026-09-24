"""Calibration methods for probability outputs (JH-63.2).

Supports 'none', 'platt' (logistic regression), and 'isotonic'.
Calibration models must be fit on train/val ONLY, never on test rows.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

CalibrationMethod = Literal["none", "platt", "isotonic"]
CALIBRATION_METHODS: tuple[CalibrationMethod, ...] = ("none", "platt", "isotonic")


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
            # Platt scaling: fit logistic regression on logit(p) or raw p
            logits = np.log(p / (1.0 - p)).reshape(-1, 1)
            clf = LogisticRegression(C=1.0, solver="lbfgs")
            clf.fit(logits, y)
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
            logits = np.log(p / (1.0 - p)).reshape(-1, 1)
            return self._model.predict_proba(logits)[:, 1]
        elif self.method == "isotonic":
            return np.asarray(self._model.predict(p), dtype=float)

        return p
