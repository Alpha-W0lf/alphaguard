"""Study matrix expander and parallel runner using ProcessPoolExecutor (JH-63.2)."""

from __future__ import annotations

import itertools
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from alphaguard.ml.study_executor import execute_run, get_git_sha
from alphaguard.ml.study_mlflow import log_run_to_mlflow
from alphaguard.ml.study_promotion import (
    build_extra_seed_configs,
    evaluate_study_promotion,
    select_shortlist,
)
from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_schema import (
    ModelHyperparams,
    ParentStudyRecord,
    RunConfig,
    RunRecord,
    StudyMatrixConfig,
)

logger = logging.getLogger(__name__)


def generate_run_configs(matrix: StudyMatrixConfig) -> list[RunConfig]:
    """Cartesian product of matrix dimensions into individual RunConfigs."""
    configs: list[RunConfig] = []
    dataset_hash = matrix.dataset_hash or ""

    param_grid = itertools.product(
        matrix.seeds,
        matrix.threshold_methods,
        matrix.betas,
        matrix.calibration_methods,
        matrix.max_depths,
        matrix.etas,
        matrix.num_boost_rounds,
        matrix.scale_pos_weights,
    )

    for idx, (
        seed,
        thresh_method,
        beta,
        calib_method,
        depth,
        eta,
        rounds,
        spw,
    ) in enumerate(param_grid):
        model_params = ModelHyperparams(
            max_depth=depth,
            eta=eta,
            num_boost_round=rounds,
            scale_pos_weight=spw,
        )
        # Create a preliminary config to compute its config_hash
        prelim = RunConfig(
            study_id=matrix.study_id,
            run_id="temp",
            seed=seed,
            dataset_path=matrix.dataset_path,
            dataset_hash=dataset_hash,
            threshold_method=thresh_method,
            beta=beta,
            calibration_method=calib_method,
            model_params=model_params,
            split_policy=matrix.split_policy,
            train_frac=matrix.train_frac,
            val_frac=matrix.val_frac,
        )
        c_hash = prelim.compute_config_hash()
        run_id = f"run_{idx:03d}_{c_hash[:8]}_s{seed}"
        config = RunConfig(
            study_id=matrix.study_id,
            run_id=run_id,
            seed=seed,
            dataset_path=matrix.dataset_path,
            dataset_hash=dataset_hash,
            threshold_method=thresh_method,
            beta=beta,
            calibration_method=calib_method,
            model_params=model_params,
            split_policy=matrix.split_policy,
            train_frac=matrix.train_frac,
            val_frac=matrix.val_frac,
        )
        configs.append(config)

    return configs


def _worker_task(config: RunConfig, bundle_dir_str: str) -> RunRecord:
    """Top-level worker function pickled to ProcessPoolExecutor processes."""
    bundle_dir = Path(bundle_dir_str)
    return execute_run(config, bundle_dir)


def run_study(
    matrix: StudyMatrixConfig,
    registry_root: Path | str = "artifacts/runs",
    max_workers: int = 1,
    matrix_source_path: str | None = None,
    existing_study_dir: Path | str | None = None,
) -> tuple[ParentStudyRecord, list[RunRecord]]:
    """Execute all matrix runs in parallel (or sequential) and persist to registry."""
    registry = StudyRegistry(registry_root)
    registry.ensure_study_dirs(matrix.study_id)

    run_records: list[RunRecord] = []
    if existing_study_dir is not None:
        source_dir = Path(existing_study_dir)
        source_registry = StudyRegistry(source_dir.parent.parent)
        run_records = source_registry.list_runs(matrix.study_id)
        configs = []
    else:
        configs = generate_run_configs(matrix)
        run_records = []
    git_sha = get_git_sha()

    total_runs = len(configs) if existing_study_dir is None else len(run_records)
    child_ids = (
        [c.run_id for c in configs]
        if existing_study_dir is None
        else [r.run_id for r in run_records]
    )

    parent = ParentStudyRecord(
        study_id=matrix.study_id,
        description=matrix.description,
        git_sha=git_sha,
        dataset_hash=matrix.dataset_hash or "",
        dataset_path=matrix.dataset_path,
        matrix_source_path=matrix_source_path,
        total_runs=total_runs,
        child_run_ids=child_ids,
    )
    registry.save_study(parent)

    bundles_dir = registry.bundles_dir(matrix.study_id)

    if max_workers <= 1 or len(configs) <= 1:
        for cfg in configs:
            b_dir = bundles_dir / cfg.run_id
            rec = execute_run(cfg, b_dir)
            registry.save_run(rec)
            if matrix.enable_mlflow:
                log_run_to_mlflow(rec, tracking_uri=matrix.mlflow_tracking_uri)
            run_records.append(rec)
    else:
        mp_ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=max_workers, mp_context=mp_ctx) as executor:
            future_to_cfg = {
                executor.submit(_worker_task, cfg, str(bundles_dir / cfg.run_id)): cfg
                for cfg in configs
            }
            for future in as_completed(future_to_cfg):
                rec = future.result()
                registry.save_run(rec)
                if matrix.enable_mlflow:
                    log_run_to_mlflow(rec, tracking_uri=matrix.mlflow_tracking_uri)
                run_records.append(rec)

    # Sort records deterministically by run_id
    run_records.sort(key=lambda r: r.run_id)

    # Multi-seed promotion gate stage (JH-AG-93.1)
    if matrix.promotion and matrix.promotion.enabled:
        shortlist = select_shortlist(
            run_records,
            top_k=matrix.promotion.shortlist_top_k,
            sort_by=matrix.promotion.sort_by,
        )
        extra_configs = build_extra_seed_configs(
            shortlist=shortlist,
            extra_seeds=matrix.promotion.extra_seeds,
            existing_runs=run_records,
            study_id=matrix.study_id,
            start_index=len(run_records),
        )

        if extra_configs:
            logger.info(
                "Scheduling %d extra-seed run(s) across %d candidate(s)...",
                len(extra_configs),
                len(shortlist),
            )
            # Update parent with expanded total_runs and child_run_ids
            parent.total_runs += len(extra_configs)
            parent.child_run_ids.extend([c.run_id for c in extra_configs])
            registry.save_study(parent)

            if max_workers <= 1 or len(extra_configs) <= 1:
                for cfg in extra_configs:
                    b_dir = bundles_dir / cfg.run_id
                    rec = execute_run(cfg, b_dir)
                    rec.stage = "extra_seed"
                    registry.save_run(rec)
                    if matrix.enable_mlflow:
                        log_run_to_mlflow(rec, tracking_uri=matrix.mlflow_tracking_uri)
                    run_records.append(rec)
            else:
                mp_ctx = mp.get_context("spawn")
                with ProcessPoolExecutor(max_workers=max_workers, mp_context=mp_ctx) as executor:
                    future_to_cfg = {
                        executor.submit(_worker_task, cfg, str(bundles_dir / cfg.run_id)): cfg
                        for cfg in extra_configs
                    }
                    for future in as_completed(future_to_cfg):
                        rec = future.result()
                        rec.stage = "extra_seed"
                        registry.save_run(rec)
                        if matrix.enable_mlflow:
                            log_run_to_mlflow(rec, tracking_uri=matrix.mlflow_tracking_uri)
                        run_records.append(rec)

            run_records.sort(key=lambda r: r.run_id)

        # Evaluate promotion status across all runs
        (
            decision,
            seeds_cleared,
            seeds_failed,
            seed_metrics_summary,
            rollup,
            notes,
        ) = evaluate_study_promotion(shortlist, run_records, matrix.promotion)

        parent.promotion_decision = decision
        parent.seeds_cleared = seeds_cleared
        parent.seeds_failed = seeds_failed
        parent.seed_metrics_summary = seed_metrics_summary
        parent.promotion_rollup = rollup
        parent.notes = notes

    # Finalize parent study record
    completed = sum(1 for r in run_records if not r.aborted)
    aborted = sum(1 for r in run_records if r.aborted)
    first_hash = run_records[0].dataset_hash if run_records else (matrix.dataset_hash or "")

    parent.completed_at = datetime.now(UTC).isoformat()
    parent.completed_runs = completed
    parent.aborted_runs = aborted
    parent.dataset_hash = first_hash
    registry.save_study(parent)

    return parent, run_records
