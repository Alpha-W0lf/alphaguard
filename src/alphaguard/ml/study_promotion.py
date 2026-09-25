"""Auto multi-seed promotion gate and deterministic shortlist selection (JH-AG-93.1).

Enforces:
1. Deterministic ranking of discovery runs (locked-test F1 -> Precision -> AUPRC -> run_id).
2. Seed-agnostic hparam signature identification for top-k candidate selection.
3. Multi-seed floor validation: every extra seed must clear all three floors
   (F1 >= 0.30, Precision >= 0.25, AUPRC >= 0.18) with zero soft misses.
4. Promotion proposal: proposes 'candidate' ONLY if all extra seeds clear all floors,
   else 'rejected' (or 'none' if promotion is disabled).
5. Explicit claim hygiene: harness proposes 'candidate', never claims 'Model Quality Go'.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from alphaguard.ml.study_schema import (
    PromotionConfig,
    PromotionFloors,
    PromotionStatus,
    RunConfig,
    RunRecord,
)


def _phase_b_informational(runs: list[RunRecord]) -> str:
    """Print Phase B blocks in the proposal. Floors do not read them."""
    bits: list[str] = []
    for run in runs:
        if run.walk_forward is not None:
            agg = run.walk_forward.aggregate
            bits.append(
                f"{run.run_id} walk_forward f1_mean={agg.mean.get('f1')} "
                f"f1_min={agg.min.get('f1')} embargo_rows={run.walk_forward.embargo_rows}"
            )
        if run.economic is not None:
            locked = run.economic.locked_test
            bits.append(
                f"{run.run_id} economic stub label={run.economic.label} "
                f"model_p_at_budget={locked.precision_at_rules_budget_model} "
                f"rules_p_at_budget={locked.precision_at_rules_budget_rules} "
                f"stub_cost_model_at_budget={locked.stub_cost_model_at_budget} "
                f"stub_cost_rules={locked.stub_cost_rules}"
            )
    if not bits:
        return ""
    return " Informational Phase B blocks (floors unchanged): " + "; ".join(bits)


def evaluate_floors(
    test_f1: float,
    test_precision: float,
    test_auprc: float,
    floors: PromotionFloors,
) -> tuple[bool, list[str]]:
    """Evaluate whether test metrics clear all three floors.

    Returns (passed, failed_floor_names).
    """
    failed: list[str] = []
    # Hard threshold checks: no soft misses allowed
    if test_f1 < floors.f1:
        failed.append(f"f1 ({test_f1:.4f} < {floors.f1:.4f})")
    if test_precision < floors.precision:
        failed.append(f"precision ({test_precision:.4f} < {floors.precision:.4f})")
    if test_auprc < floors.auprc:
        failed.append(f"auprc ({test_auprc:.4f} < {floors.auprc:.4f})")

    return (len(failed) == 0, failed)


def compute_hparam_signature(config: RunConfig) -> str:
    """Compute a deterministic hash of seed-agnostic hyperparameter settings."""
    raw = {
        "threshold_method": config.threshold_method,
        "beta": round(config.beta, 4),
        "calibration_method": config.calibration_method,
        "model_params": config.model_params.model_dump(),
        "split_policy": config.split_policy,
        "train_frac": round(config.train_frac, 4),
        "val_frac": round(config.val_frac, 4),
        "dataset_path": config.dataset_path,
        "dataset_hash": config.dataset_hash,
    }
    dumped = json.dumps(raw, sort_keys=True).encode("utf-8")
    return hashlib.sha256(dumped).hexdigest()[:16]


def get_run_metrics(run: RunRecord) -> tuple[float, float, float]:
    """Extract (test_f1, test_precision, test_auprc) from a RunRecord."""
    test_m = run.metrics.get("test")
    if not test_m or run.aborted:
        return (0.0, 0.0, 0.0)
    return (float(test_m.f1), float(test_m.precision), float(test_m.auprc))


def select_shortlist(
    runs: list[RunRecord],
    top_k: int = 3,
    sort_by: str = "test_f1",
) -> list[RunRecord]:
    """Select top_k distinct hyperparameter candidates deterministically.

    Ranking policy:
    - Exclude aborted runs.
    - Default sort: (-test_f1, -test_precision, -test_auprc, run_id).
    - Preserves deterministic tie-breaking.
    - Shortlists at most one representative run per unique hparam signature.
    """
    valid_runs = [r for r in runs if not r.aborted and "test" in r.metrics]

    def _sort_key(r: RunRecord) -> tuple[float, float, float, str]:
        f1, p, auprc = get_run_metrics(r)
        if sort_by == "test_p":
            return (-p, -f1, -auprc, r.run_id)
        if sort_by == "test_auprc":
            return (-auprc, -f1, -p, r.run_id)
        # Default: test_f1
        return (-f1, -p, -auprc, r.run_id)

    sorted_runs = sorted(valid_runs, key=_sort_key)

    shortlist: list[RunRecord] = []
    seen_hparam_sigs: set[str] = set()

    for r in sorted_runs:
        sig = compute_hparam_signature(r.config)
        if sig not in seen_hparam_sigs:
            seen_hparam_sigs.add(sig)
            shortlist.append(r)
            if len(shortlist) >= top_k:
                break

    return shortlist


def _make_seed_config(
    base: RunConfig, study_id: str, seed: int, idx: int
) -> RunConfig:
    cfg = RunConfig(
        study_id=study_id,
        run_id="temp",
        seed=seed,
        dataset_path=base.dataset_path,
        dataset_hash=base.dataset_hash,
        threshold_method=base.threshold_method,
        beta=base.beta,
        calibration_method=base.calibration_method,
        model_params=base.model_params.model_copy(),
        split_policy=base.split_policy,
        train_frac=base.train_frac,
        val_frac=base.val_frac,
    )
    c_hash = cfg.compute_config_hash()
    cfg.run_id = f"run_{idx:03d}_{c_hash[:8]}_s{seed}"
    return cfg


def build_extra_seed_configs(
    shortlist: list[RunRecord],
    extra_seeds: list[int],
    existing_runs: list[RunRecord],
    study_id: str,
    start_index: int = 0,
) -> list[RunConfig]:
    """Create RunConfigs for shortlisted candidates across required extra seeds.

    Skips any (hparam, seed) combination that already completed in existing_runs.
    """
    existing_pairs: set[tuple[str, int]] = {
        (compute_hparam_signature(r.config), r.seed)
        for r in existing_runs
        if not r.aborted
    }

    new_configs: list[RunConfig] = []
    idx = start_index

    for candidate in shortlist:
        hparam_sig = compute_hparam_signature(candidate.config)
        for seed in extra_seeds:
            if (hparam_sig, seed) not in existing_pairs:
                new_configs.append(
                    _make_seed_config(candidate.config, study_id, seed, idx)
                )
                idx += 1

    return new_configs


def _eval_candidate_seed(
    run: RunRecord | None,
    seed: int,
    is_extra: bool,
    floors: PromotionFloors,
) -> tuple[bool, bool, dict[str, Any]]:
    """Evaluate a single seed run against floors.

    Returns (cleared, extra_passed, eval_dict).
    """
    if run is None or run.aborted:
        return (
            False,
            not is_extra,
            {
                "seed": seed,
                "is_extra": is_extra,
                "run_id": run.run_id if run else None,
                "passed": False,
                "failed_floors": ["missing_or_aborted"],
            },
        )
    f1, p, auprc = get_run_metrics(run)
    passed, failed = evaluate_floors(f1, p, auprc, floors)
    conf = run.confusion.model_dump() if run.confusion else None
    res = {
        "seed": seed,
        "is_extra": is_extra,
        "run_id": run.run_id,
        "test_f1": round(f1, 4),
        "test_precision": round(p, 4),
        "test_auprc": round(auprc, 4),
        "passed": passed,
        "failed_floors": failed,
        "confusion": conf,
        "n_pos_test": run.n_positive_test,
    }
    return (passed, passed if is_extra else True, res)


def evaluate_study_promotion(
    shortlist: list[RunRecord],
    all_runs: list[RunRecord],
    promotion_config: PromotionConfig,
) -> tuple[PromotionStatus, list[int], list[int], dict[str, Any], dict[str, Any], str]:
    """Evaluate multi-seed promotion gate across all shortlisted candidates.

    Returns:
    (promotion_decision, seeds_cleared, seeds_failed, seed_metrics_summary, rollup_dict, notes)
    """
    if not promotion_config.enabled or not shortlist:
        return (
            "none",
            [],
            [],
            {},
            {
                "decision": "none",
                "enabled": promotion_config.enabled,
                "notes": "Promotion gate disabled or no candidates shortlisted.",
            },
            "Promotion gate disabled or no candidates shortlisted.",
        )

    runs_by_sig_seed = {
        (compute_hparam_signature(r.config), r.seed): r
        for r in all_runs
        if not r.aborted
    }

    candidates_eval: list[dict[str, Any]] = []
    winning_candidate: dict[str, Any] | None = None
    first_candidate_summary: dict[str, Any] = {}

    for cand_idx, candidate in enumerate(shortlist):
        sig = compute_hparam_signature(candidate.config)
        required_seeds = promotion_config.extra_seeds
        all_eval_seeds = [candidate.seed] + [s for s in required_seeds if s != candidate.seed]

        cand_cleared: list[int] = []
        cand_failed: list[int] = []
        seed_evals: dict[str, Any] = {}
        all_extra_passed = True

        for seed in all_eval_seeds:
            run = runs_by_sig_seed.get((sig, seed))
            is_extra = seed in required_seeds
            cleared, extra_ok, ev = _eval_candidate_seed(
                run, seed, is_extra, promotion_config.floors
            )
            if cleared:
                cand_cleared.append(seed)
            else:
                cand_failed.append(seed)
            if not extra_ok:
                all_extra_passed = False
            seed_evals[str(seed)] = ev

        cand_record = {
            "candidate_rank": cand_idx + 1,
            "primary_run_id": candidate.run_id,
            "primary_seed": candidate.seed,
            "hparam_signature": sig,
            "config_hash": candidate.config_hash,
            "all_extra_seeds_passed": all_extra_passed,
            "seeds_cleared": cand_cleared,
            "seeds_failed": cand_failed,
            "seed_evaluations": seed_evals,
        }
        candidates_eval.append(cand_record)

        if cand_idx == 0:
            first_candidate_summary = cand_record

        if all_extra_passed and winning_candidate is None:
            winning_candidate = cand_record

    target = winning_candidate or first_candidate_summary
    seeds_cleared = target.get("seeds_cleared", [])
    seeds_failed = target.get("seeds_failed", [])
    seed_metrics_summary = target.get("seed_evaluations", {})

    if winning_candidate is not None:
        decision: PromotionStatus = "candidate"
        notes = (
            f"Promotion gate proposed 'candidate' for run '{winning_candidate['primary_run_id']}': "
            f"all required extra seeds {promotion_config.extra_seeds} cleared floors "
            f"(F1>={promotion_config.floors.f1}, P>={promotion_config.floors.precision}, "
            f"AUPRC>={promotion_config.floors.auprc}). Human Model Quality Go review required."
        )
    else:
        decision = "rejected"
        notes = (
            f"Promotion gate rejected: no shortlisted candidate cleared all required extra seeds "
            f"{promotion_config.extra_seeds} across floors "
            f"(F1>={promotion_config.floors.f1}, P>={promotion_config.floors.precision}, "
            f"AUPRC>={promotion_config.floors.auprc})."
        )
    notes += _phase_b_informational(all_runs)

    rollup = {
        "decision": decision,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "floors": promotion_config.floors.model_dump(),
        "shortlist_top_k": promotion_config.shortlist_top_k,
        "extra_seeds": promotion_config.extra_seeds,
        "candidates": candidates_eval,
        "winning_candidate_hash": (
            winning_candidate["hparam_signature"] if winning_candidate else None
        ),
        "notes": notes,
    }

    return (
        decision,
        seeds_cleared,
        seeds_failed,
        seed_metrics_summary,
        rollup,
        notes,
    )
