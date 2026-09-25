"""Shared slices for the Phase C label and data audit.

The recorded Phase B split is four expanding folds inside the first 80 percent
of rows, a 5-global-row embargo, and a locked test on the last 20 percent.
These helpers only slice that split. They do not fit a model.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaguard.ml.study_walkforward import FoldIndex, expanding4_folds

FREEZE_HASH = "534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3"
LABEL_HORIZON_SESSIONS = 5


def recorded_folds(n_rows: int) -> tuple[list[FoldIndex], int]:
    """Phase B indices: embargo of 5 global rows, dev prefix at 80 percent."""
    folds, n_dev, _source = expanding4_folds(n_rows, embargo_rows=LABEL_HORIZON_SESSIONS)
    return folds, n_dev


def slice_bounds(folds: list[FoldIndex], n_rows: int, n_dev: int) -> list[dict[str, Any]]:
    """Val blocks plus the locked test. Train gaps are not slices."""
    bounds: list[dict[str, Any]] = []
    for fold in folds:
        bounds.append(
            {
                "name": f"fold_{fold.fold}",
                "fold": fold.fold,
                "start": fold.val_start,
                "end": fold.val_end,
                "kind": "fold",
            }
        )
    bounds.append(
        {
            "name": "locked_test",
            "fold": None,
            "start": n_dev,
            "end": n_rows,
            "kind": "locked_test",
        }
    )
    return bounds


def prevalence(y: np.ndarray) -> float:
    n = int(len(y))
    if n == 0:
        return 0.0
    return float(np.asarray(y).sum() / n)


def feature_dates(df: pd.DataFrame) -> pd.Series:
    return df["feature_as_of"].map(lambda value: pd.Timestamp(value).date())


def json_float(value: float | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    if number != number:  # NaN
        return None
    return number
