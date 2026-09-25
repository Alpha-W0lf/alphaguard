"""WP-C4: label versus the prior-return rules veto.

The rules alert is ``return_5d_prior < -0.03`` (the Phase B baseline).
Aligned means the positive rate inside the veto set is higher than outside
it on at least 3 of the 4 walk-forward folds. The locked test is reported
and is not part of that count. A tie is not higher.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from alphaguard.ml.audit_common import json_float, slice_bounds
from alphaguard.ml.study_economic import derive_rules_alerts
from alphaguard.ml.study_walkforward import FoldIndex


def _rates(y: np.ndarray, rules: np.ndarray) -> dict[str, Any]:
    veto = y[rules]
    quiet = y[~rules]
    veto_rate = float(veto.mean()) if len(veto) else None
    quiet_rate = float(quiet.mean()) if len(quiet) else None
    higher = (
        veto_rate is not None and quiet_rate is not None and veto_rate > quiet_rate
    )
    return {
        "n": int(len(y)),
        "n_veto": int(rules.sum()),
        "veto_positive_rate": json_float(veto_rate),
        "non_veto_positive_rate": json_float(quiet_rate),
        "veto_higher": higher,
    }


def audit_rules_alignment(
    df: pd.DataFrame,
    folds: list[FoldIndex],
    n_dev: int,
) -> dict[str, Any]:
    rules, spec, spec_hash = derive_rules_alerts(df)
    y = df["label_high_risk"].to_numpy(dtype=int)
    rows: list[dict[str, Any]] = []
    fold_higher = 0
    fold_count = 0
    for bound in slice_bounds(folds, len(df), n_dev):
        sl = slice(bound["start"], bound["end"])
        row = _rates(y[sl], rules[sl])
        row["name"] = bound["name"]
        rows.append(row)
        if bound["kind"] == "fold":
            fold_count += 1
            if row["veto_higher"]:
                fold_higher += 1
    aligned = fold_count > 0 and fold_higher >= 3
    return {
        "rules_spec": spec,
        "rules_fn_hash": spec_hash,
        "slices": rows,
        "folds_veto_higher": fold_higher,
        "fold_count": fold_count,
        "verdict": "aligned" if aligned else "misaligned",
    }
