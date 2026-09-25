"""WP-C1: label semantics on a frozen training frame.

Rule: ``label_high_risk`` is 1 iff ``fwd_return_5d < -0.03``. The value
``-0.03`` is 0. The return is a fraction from the first completed session
close at or after the event to the close five XNYS sessions later. Splits
and dividends sit in the auto-adjusted close. A missing close drops the row.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaguard.ml.audit_common import json_float, prevalence, slice_bounds
from alphaguard.ml.dataset_asof import LABEL_THRESHOLD, label_high_risk_from_fwd
from alphaguard.ml.study_walkforward import FoldIndex


def recomputed_labels(fwd_return: pd.Series) -> np.ndarray:
    return fwd_return.map(label_high_risk_from_fwd).to_numpy(dtype=int)


def label_mismatch_rows(df: pd.DataFrame) -> list[int]:
    """Row positions where the frozen label disagrees with the threshold rule."""
    if "fwd_return_5d" not in df.columns or "label_high_risk" not in df.columns:
        raise ValueError("frame needs fwd_return_5d and label_high_risk")
    frozen = df["label_high_risk"].to_numpy(dtype=int)
    fresh = recomputed_labels(df["fwd_return_5d"])
    return [int(i) for i in np.flatnonzero(fresh != frozen)]


def audit_labels(
    df: pd.DataFrame,
    folds: list[FoldIndex],
    n_dev: int,
) -> dict[str, Any]:
    mismatches = label_mismatch_rows(df)
    y = df["label_high_risk"].to_numpy(dtype=int)
    by_slice: list[dict[str, Any]] = []
    for bound in slice_bounds(folds, len(df), n_dev):
        part = y[bound["start"] : bound["end"]]
        by_slice.append(
            {
                "name": bound["name"],
                "n": int(len(part)),
                "n_positive": int(part.sum()),
                "prevalence": json_float(prevalence(part)),
            }
        )
    return {
        "threshold": LABEL_THRESHOLD,
        "units": "fraction",
        "anchor": "first_completed_session_close_at_or_after_event",
        "horizon_trading_sessions": 5,
        "corporate_actions": "yfinance auto_adjust=True closes (splits and dividends)",
        "halts_and_delistings": "missing close drops the row; no imputed return",
        "equality_at_threshold_is_negative": True,
        "n_rows": int(len(df)),
        "mismatch_count": len(mismatches),
        "mismatch_rows": mismatches,
        "prevalence_full": json_float(prevalence(y)),
        "slices": by_slice,
    }
