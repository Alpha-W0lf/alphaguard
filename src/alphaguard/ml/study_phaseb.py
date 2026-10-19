"""Phase B attach, summarize, and promote. Floors are not changed here.

Promote prints `candidate` or `no candidate`. It does not claim a quality gate.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from alphaguard.ml.study_economic import (
    build_economic_block,
    derive_rules_alerts,
    economic_split,
)
from alphaguard.ml.study_promotion import evaluate_floors
from alphaguard.ml.study_schema import (
    SCHEMA_VERSION_PHASE_B,
    EconomicBlock,
    PromotionFloors,
    RunConfig,
    RunRecord,
    WalkForwardBlock,
)
from alphaguard.ml.study_walkforward import FoldScore, evaluate_expanding4

logger = logging.getLogger(__name__)


def attach_phase_b(
    *,
    df: pd.DataFrame,
    config: RunConfig,
    y_test: np.ndarray,
    test_probs: np.ndarray,
    test_threshold: float,
    walk_forward: str,
    economic: str,
    cost_fp: float,
    cost_fn: float,
    embargo_rows: int | None,
) -> tuple[str, WalkForwardBlock | None, EconomicBlock | None]:
    """Return (schema_version, walk_forward block or None, economic block or None)."""
    if walk_forward not in ("off", "expanding4"):
        raise ValueError(f"walk_forward must be off or expanding4, got {walk_forward!r}")
    if economic not in ("off", "on"):
        raise ValueError(f"economic must be off or on, got {economic!r}")

    n_dev = len(df) - len(y_test)
    wf_block: WalkForwardBlock | None = None
    fold_scores: list[FoldScore] = []
    if walk_forward == "expanding4":
        wf_block, fold_scores = evaluate_expanding4(
            df, config, n_dev=n_dev, embargo_rows=embargo_rows
        )

    econ_block: EconomicBlock | None = None
    if economic == "on":
        rules, spec, spec_hash = derive_rules_alerts(df)
        if len(rules) != len(df):
            raise ValueError("rules mask length does not match the frame")
        fold_parts = []
        for scored in fold_scores:
            idx = scored.index
            fold_parts.append(
                economic_split(
                    scored.y_val,
                    scored.probs_val,
                    rules[idx.val_start : idx.val_end],
                    scored.threshold,
                    cost_fp=cost_fp,
                    cost_fn=cost_fn,
                )
            )
        locked = economic_split(
            y_test,
            test_probs,
            rules[n_dev:],
            test_threshold,
            cost_fp=cost_fp,
            cost_fn=cost_fn,
        )
        econ_block = build_economic_block(
            rules_spec=spec,
            rules_fn=spec_hash,
            rules_mask=rules,
            fold_parts=fold_parts,
            locked_test=locked,
            cost_fp=cost_fp,
            cost_fn=cost_fn,
        )
    if wf_block is None and econ_block is None:
        raise ValueError("phase B attach called with both blocks off")
    return SCHEMA_VERSION_PHASE_B, wf_block, econ_block


def load_phaseb_runs(out_dir: Path) -> list[RunRecord]:
    paths = sorted(Path(out_dir).rglob("run.json"))
    return [RunRecord.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]


def phase_c_trigger(
    seed_fold_f1: list[list[float]],
    seed_fold_pos: list[list[float]],
    seed_test_f1: list[float],
) -> dict[str, object]:
    """Diagnostic only. Fires if fold positive rates vary >2× or fold F1 std > seed F1 std."""
    ratios: list[float] = []
    rate_fired = False
    for rates in seed_fold_pos:
        if not rates:
            continue
        lo, hi = min(rates), max(rates)
        if lo <= 0.0:
            ratio = float("inf") if hi > 0.0 else 1.0
        else:
            ratio = hi / lo
        ratios.append(ratio)
        if ratio > 2.0:
            rate_fired = True

    n_folds = max((len(row) for row in seed_fold_f1), default=0)
    fold_means: list[float] = []
    for i in range(n_folds):
        vals = [row[i] for row in seed_fold_f1 if len(row) > i]
        if vals:
            fold_means.append(float(np.mean(vals)))
    fold_std = float(np.std(fold_means, ddof=1)) if len(fold_means) >= 2 else 0.0
    seed_std = float(np.std(seed_test_f1, ddof=1)) if len(seed_test_f1) >= 2 else 0.0
    std_fired = fold_std > seed_std
    return {
        "fired": bool(rate_fired or std_fired),
        "positive_rate_max_over_min": ratios,
        "fold_to_fold_std_f1": fold_std,
        "seed_to_seed_std_f1": seed_std,
        "positive_rate_varies_gt_2x": rate_fired,
        "fold_std_gt_seed_std": std_fired,
    }


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def summarize_phaseb(out_dir: Path) -> str:
    """Markdown summary. Does not propose or claim a quality decision."""
    runs = load_phaseb_runs(out_dir)
    lines: list[str] = [
        "# Phase B summary",
        "",
        "Harness evidence only. This file does not claim a quality decision.",
        "",
        "## Per-seed × per-fold",
        "",
        "| seed | fold | F1 | P | AUPRC | positive_rate | n_rows |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    seed_fold_f1: list[list[float]] = []
    seed_fold_pos: list[list[float]] = []
    seed_test_f1: list[float] = []
    for run in runs:
        wf = run.walk_forward
        if wf is None:
            lines.append(f"| {run.seed} | n/a | n/a | n/a | n/a | n/a | n/a |")
            seed_fold_f1.append([])
            seed_fold_pos.append([])
        else:
            f1s: list[float] = []
            rates: list[float] = []
            for fold in wf.folds:
                lines.append(
                    f"| {run.seed} | {fold.fold} | {_fmt(fold.f1)} | {_fmt(fold.precision)} "
                    f"| {_fmt(fold.auprc)} | {_fmt(fold.positive_rate)} | {fold.n_rows} |"
                )
                f1s.append(fold.f1)
                rates.append(fold.positive_rate)
            seed_fold_f1.append(f1s)
            seed_fold_pos.append(rates)
        test = run.metrics.get("test")
        seed_test_f1.append(float(test.f1) if test is not None and not run.aborted else float("nan"))

    floors = PromotionFloors()
    lines.extend(
        [
            "",
            "## Locked-test floors",
            "",
            f"Floors unchanged: F1 ≥ {floors.f1:.2f}, P ≥ {floors.precision:.2f}, "
            f"AUPRC ≥ {floors.auprc:.2f}.",
            "",
            "| seed | F1 | P | AUPRC | floors |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for run in runs:
        test = run.metrics.get("test")
        if run.aborted or test is None:
            lines.append(f"| {run.seed} | n/a | n/a | n/a | FAIL |")
            continue
        ok, failed = evaluate_floors(test.f1, test.precision, test.auprc, floors)
        status = "pass" if ok else "fail (" + ", ".join(failed) + ")"
        lines.append(
            f"| {run.seed} | {_fmt(test.f1)} | {_fmt(test.precision)} | {_fmt(test.auprc)} | {status} |"
        )

    lines.extend(
        [
            "",
            "## Rules vs model at budget",
            "",
            "| seed | split | precision_model | precision_rules | stub_cost_model | stub_cost_rules |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for run in runs:
        econ = run.economic
        if econ is None:
            lines.append(f"| {run.seed} | n/a | n/a | n/a | n/a | n/a |")
            continue
        for i, fold in enumerate(econ.folds):
            lines.append(
                f"| {run.seed} | fold {i} | {_fmt(fold.precision_at_rules_budget_model)} "
                f"| {_fmt(fold.precision_at_rules_budget_rules)} "
                f"| {_fmt(fold.stub_cost_model_at_budget)} | {_fmt(fold.stub_cost_rules)} |"
            )
        locked = econ.locked_test
        lines.append(
            f"| {run.seed} | locked_test | {_fmt(locked.precision_at_rules_budget_model)} "
            f"| {_fmt(locked.precision_at_rules_budget_rules)} "
            f"| {_fmt(locked.stub_cost_model_at_budget)} | {_fmt(locked.stub_cost_rules)} |"
        )

    finite_test = [v for v in seed_test_f1 if v == v]
    trigger = phase_c_trigger(seed_fold_f1, seed_fold_pos, finite_test)
    fired = "Y" if trigger["fired"] else "N"
    lines.extend(
        [
            "",
            "## Per-fold positive rate",
            "",
            "See the per-seed × per-fold table (`positive_rate` column). Diagnostic only.",
            "",
            "## Phase C trigger",
            "",
            f"- fired: {fired}",
            f"- positive_rate max/min per seed: {trigger['positive_rate_max_over_min']}",
            f"- fold_to_fold_std_f1: {trigger['fold_to_fold_std_f1']}",
            f"- seed_to_seed_std_f1: {trigger['seed_to_seed_std_f1']}",
            f"- positive_rate_varies_gt_2x: {trigger['positive_rate_varies_gt_2x']}",
            f"- fold_std_gt_seed_std: {trigger['fold_std_gt_seed_std']}",
            "",
        ]
    )
    return "\n".join(lines)


def promote_phaseb(out_dir: Path) -> str:
    """Propose candidate or no candidate from locked-test floors only."""
    runs = load_phaseb_runs(out_dir)
    floors = PromotionFloors()
    all_clear = bool(runs)
    detail: list[str] = []
    for run in runs:
        test = run.metrics.get("test")
        if run.aborted or test is None:
            all_clear = False
            reason = run.abort_reason or "missing_or_aborted"
            detail.append(f"seed {run.seed}: FAIL {reason}")
            continue
        ok, failed = evaluate_floors(test.f1, test.precision, test.auprc, floors)
        if not ok:
            all_clear = False
        status = "pass" if ok else "fail " + ", ".join(failed)
        detail.append(f"seed {run.seed}: {status}")
        if run.walk_forward is not None:
            agg = run.walk_forward.aggregate
            detail.append(
                f"  walk_forward informational f1_mean={agg.mean.get('f1')} "
                f"f1_min={agg.min.get('f1')} embargo_rows={run.walk_forward.embargo_rows}"
            )
        if run.economic is not None:
            locked = run.economic.locked_test
            detail.append(
                "  economic stub informational "
                f"precision_model={locked.precision_at_rules_budget_model} "
                f"precision_rules={locked.precision_at_rules_budget_rules} "
                f"stub_cost_model={locked.stub_cost_model_at_budget} "
                f"stub_cost_rules={locked.stub_cost_rules} "
                f"label={run.economic.label}"
            )
    decision = "candidate" if all_clear else "no candidate"
    logger.info("phase B promote decision=%s runs=%s", decision, len(runs))
    return decision + "\n" + "\n".join(detail) + ("\n" if detail else "")
