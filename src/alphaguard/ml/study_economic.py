"""Rules-only economic stub at a matched alert budget (Phase B).

Costs are unitless (`label="stub"`). No dollar figures.

Rules baseline: there is no stored rules column on the training frame.
The pure function is the existing deterministic vol veto
(`volatility_20d >= 0.05`, the eval-harness gate constant). No model and no seed.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from alphaguard.ml.study_schema import EconomicBlock, EconomicSplit, ShadowAgreement

# Same constant as eval.harness.build_vol_veto_gate. Not fit on labels.
VOL_VETO_THRESHOLD = 0.05
RULES_SPEC = "volatility_20d>=0.05"


def rules_fn_hash(spec: str) -> str:
    return hashlib.sha256(spec.encode("utf-8")).hexdigest()


def alert_mask_hash(mask: np.ndarray) -> str:
    raw = np.asarray(mask, dtype=np.uint8).tobytes()
    return hashlib.sha256(raw).hexdigest()


def derive_rules_alerts(df: pd.DataFrame) -> tuple[np.ndarray, str, str]:
    """Return (bool mask, spec, spec hash). Prefer a raw `rules_alert` column."""
    if "rules_alert" in df.columns:
        spec = "column:rules_alert"
        alerts = df["rules_alert"].astype(bool).to_numpy()
    else:
        if "volatility_20d" not in df.columns:
            raise ValueError("economic stub needs rules_alert or volatility_20d")
        spec = RULES_SPEC
        alerts = df["volatility_20d"].to_numpy(dtype=float) >= VOL_VETO_THRESHOLD
    return np.asarray(alerts, dtype=bool), spec, rules_fn_hash(spec)


def topk_alert(scores: np.ndarray, k: int) -> np.ndarray:
    """Alert on the top-k scores. Ties keep the earlier row (stable mergesort)."""
    scores = np.asarray(scores, dtype=float)
    n = len(scores)
    mask = np.zeros(n, dtype=bool)
    if k <= 0 or n == 0:
        return mask
    take = min(int(k), n)
    order = np.argsort(-scores, kind="mergesort")
    mask[order[:take]] = True
    return mask


def _counts(y_true: np.ndarray, alert: np.ndarray) -> tuple[int, int, int, int]:
    y = np.asarray(y_true, dtype=int)
    a = np.asarray(alert, dtype=bool)
    tp = int((a & (y == 1)).sum())
    fp = int((a & (y == 0)).sum())
    tn = int((~a & (y == 0)).sum())
    fn = int((~a & (y == 1)).sum())
    return tp, fp, tn, fn


def _precision_recall(tp: int, fp: int, fn: int) -> tuple[float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall


def stub_cost(fp: int, fn: int, cost_fp: float, cost_fn: float) -> float:
    return float(cost_fp) * int(fp) + float(cost_fn) * int(fn)


def economic_split(
    y_true: np.ndarray,
    scores: np.ndarray,
    rules_alert: np.ndarray,
    threshold: float,
    *,
    cost_fp: float,
    cost_fn: float,
) -> EconomicSplit:
    """Matched budget k = rules alerts. Model top-k is compared to that mask."""
    y = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    rules = np.asarray(rules_alert, dtype=bool)
    if not (len(y) == len(scores) == len(rules)):
        raise ValueError("y, scores, and rules_alert must be the same length")
    k = int(rules.sum())
    at_threshold = scores >= float(threshold)
    at_budget = topk_alert(scores, k)
    tp_t, fp_t, _tn_t, fn_t = _counts(y, at_threshold)
    tp_b, fp_b, _tn_b, fn_b = _counts(y, at_budget)
    tp_r, fp_r, _tn_r, fn_r = _counts(y, rules)
    p_model, r_model = _precision_recall(tp_b, fp_b, fn_b)
    p_rules, r_rules = _precision_recall(tp_r, fp_r, fn_r)
    n = len(y)
    return EconomicSplit(
        rules_alerts=k,
        model_alerts_at_threshold=int(at_threshold.sum()),
        precision_at_rules_budget_model=p_model,
        recall_at_rules_budget_model=r_model,
        precision_at_rules_budget_rules=p_rules,
        recall_at_rules_budget_rules=r_rules,
        incremental_tp=int(((y == 1) & at_budget & ~rules).sum()),
        rules_only_tp=int(((y == 1) & rules & ~at_budget).sum()),
        stub_cost_model_at_threshold=stub_cost(fp_t, fn_t, cost_fp, cost_fn),
        stub_cost_model_at_budget=stub_cost(fp_b, fn_b, cost_fp, cost_fn),
        stub_cost_rules=stub_cost(fp_r, fn_r, cost_fp, cost_fn),
        shadow_agreement=ShadowAgreement(
            model_alert_rules_alert=int((at_budget & rules).sum()),
            model_alert_rules_quiet=int((at_budget & ~rules).sum()),
            model_quiet_rules_alert=int((~at_budget & rules).sum()),
            model_quiet_rules_quiet=int((~at_budget & ~rules).sum()),
        ),
        n_rows=n,
        positive_rate=float(y.sum() / n) if n else 0.0,
    )


def build_economic_block(
    *,
    rules_spec: str,
    rules_fn: str,
    rules_mask: np.ndarray,
    fold_parts: list[EconomicSplit],
    locked_test: EconomicSplit,
    cost_fp: float,
    cost_fn: float,
) -> EconomicBlock:
    return EconomicBlock(
        label="stub",
        cost_fp=float(cost_fp),
        cost_fn=float(cost_fn),
        rules_spec=rules_spec,
        rules_fn_hash=rules_fn,
        rules_mask_hash=alert_mask_hash(rules_mask),
        folds=fold_parts,
        locked_test=locked_test,
    )
