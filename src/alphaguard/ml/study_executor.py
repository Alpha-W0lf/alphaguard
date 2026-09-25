"""Single experiment run executor with strict leakage discipline (JH-63.2).

Guarantees:
1. HPO, threshold fitting, and calibration fit ONLY on train/val.
2. The locked held-out test split is scored ONCE at the end.
3. Dataset hash is verified prior to training.
4. Each run writes isolated artifacts to its own bundle_dir.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.contracts.manifest import LabelWindow, ModelBundleManifest, TrainWindow
from alphaguard.ml.study_calibration import ProbabilityCalibrator
from alphaguard.ml.study_metrics import compute_metrics_suite
from alphaguard.ml.study_schema import (
    ConfusionMatrix,
    RunConfig,
    RunRecord,
    SplitMetrics,
)
from alphaguard.ml.study_walkforward import split_for_walk_forward
from alphaguard.ml.train_eval import (
    METHOD_TRAIN_F1_MAX,
    VAL_SINGLE_CLASS_REASON,
    fit_threshold_train_f1,
    fit_threshold_train_val_fbeta,
    train_val_sizes,
)
from alphaguard.ml.train_hpo import FIXED_PARAMS
from alphaguard.ml.train_option_b import (
    atomic_write_bundle,
    dataset_hash,
    load_training_frame,
)

logger = logging.getLogger(__name__)


def get_git_sha() -> str:
    """Resolve current git commit SHA, falling back to 'unknown'."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=5
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


def _build_booster_params(
    config: RunConfig, scale_pos_weight: float
) -> dict[str, Any]:
    params = {
        **FIXED_PARAMS,
        "seed": config.seed,
        "max_depth": config.model_params.max_depth,
        "eta": config.model_params.eta,
        "subsample": config.model_params.subsample,
        "colsample_bytree": config.model_params.colsample_bytree,
        "reg_lambda": config.model_params.reg_lambda,
        "scale_pos_weight": (
            config.model_params.scale_pos_weight
            if config.model_params.scale_pos_weight is not None
            else scale_pos_weight
        ),
    }
    return params


def execute_run(
    config: RunConfig,
    bundle_dir: Path,
    *,
    walk_forward: str = "off",
    economic: str = "off",
    cost_fp: float = 1.0,
    cost_fn: float = 10.0,
    embargo_rows: int | None = None,
) -> RunRecord:
    """Execute a single run configuration end-to-end with strict leakage guards."""
    start_time = time.time()
    git_sha = get_git_sha()
    config_hash = config.compute_config_hash()

    def _abort(reason: str, d_hash: str = "") -> RunRecord:
        return RunRecord(
            run_id=config.run_id,
            study_id=config.study_id,
            git_sha=git_sha,
            dataset_hash=d_hash or config.dataset_hash,
            config_hash=config_hash,
            seed=config.seed,
            threshold_method=config.threshold_method,
            calibration_method=config.calibration_method,
            split_policy=config.split_policy,
            score_threshold=0.5,
            wall_time_s=time.time() - start_time,
            aborted=True,
            abort_reason=reason,
            bundle_dir=str(bundle_dir),
            config=config,
        )

    parquet_path = Path(config.dataset_path)
    if not parquet_path.exists():
        return _abort(f"Dataset parquet not found: {parquet_path}")

    try:
        df = load_training_frame(parquet_path)
    except Exception as exc:
        return _abort(f"Failed loading parquet: {exc}")

    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    actual_hash = dataset_hash(x_all, y_all)

    # Dataset hash mismatch check
    if config.dataset_hash and config.dataset_hash != actual_hash:
        return _abort(
            f"Dataset hash mismatch: expected {config.dataset_hash}, got {actual_hash}",
            d_hash=actual_hash,
        )

    try:
        split = split_for_walk_forward(df, config.train_frac, walk_forward)
    except Exception as exc:
        return _abort(f"Time-ordered split failed: {exc}", d_hash=actual_hash)

    n_pos_train = int(split.y_train.sum())
    n_neg_train = int(len(split.y_train) - n_pos_train)
    if n_pos_train == 0:
        return _abort(
            "n_pos_train==0 — cannot compute default scale_pos_weight", d_hash=actual_hash
        )

    default_spw = float(n_neg_train) / float(n_pos_train)
    params = _build_booster_params(config, default_spw)

    # Train model booster on train partition only
    dtrain = xgb.DMatrix(split.x_train, label=split.y_train, feature_names=list(FEATURE_NAMES))
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=config.model_params.num_boost_round,
    )

    raw_train_probs = booster.predict(dtrain)

    # Inner val partition for threshold/calibration if requested
    n_fit, n_val = train_val_sizes(len(split.y_train), val_frac=config.val_frac)
    y_fit, y_val = split.y_train[:n_fit], split.y_train[n_fit:]
    x_fit, x_val = split.x_train[:n_fit], split.x_train[n_fit:]
    n_pos_val = int(y_val.sum())

    # Calibration fitting: train/val only!
    calibrator = ProbabilityCalibrator(config.calibration_method)
    if config.calibration_method != "none":
        # Fit calibrator on train prefix or val
        if len(np.unique(y_val)) >= 2:
            # Predict val with auxiliary booster trained on fit prefix only
            spw_fit = float(len(y_fit) - y_fit.sum()) / float(max(1, y_fit.sum()))
            fit_params = _build_booster_params(config, spw_fit)
            dfit = xgb.DMatrix(x_fit, label=y_fit, feature_names=list(FEATURE_NAMES))
            aux_booster = xgb.train(
                fit_params, dfit, num_boost_round=config.model_params.num_boost_round
            )
            dval = xgb.DMatrix(x_val, feature_names=list(FEATURE_NAMES))
            val_raw_p = aux_booster.predict(dval)
            calibrator.fit(val_raw_p, y_val)
        else:
            # Fall back to fitting on train prefix
            calibrator.fit(raw_train_probs, split.y_train)

    train_probs = calibrator.predict_proba(raw_train_probs)

    # Threshold selection: train or val ONLY! Never test.
    aborted_experiment = False
    abort_reason = None
    if config.threshold_method == METHOD_TRAIN_F1_MAX:
        threshold = fit_threshold_train_f1(split.y_train, train_probs)
        actual_method = METHOD_TRAIN_F1_MAX
    elif config.threshold_method.startswith("train_val_fbeta"):
        if len(np.unique(y_val)) < 2:
            aborted_experiment = True
            abort_reason = VAL_SINGLE_CLASS_REASON
            threshold = fit_threshold_train_f1(split.y_train, train_probs)
            actual_method = METHOD_TRAIN_F1_MAX
        else:
            spw_fit = float(len(y_fit) - y_fit.sum()) / float(max(1, y_fit.sum()))
            fit_params = _build_booster_params(config, spw_fit)
            dfit = xgb.DMatrix(x_fit, label=y_fit, feature_names=list(FEATURE_NAMES))
            aux_booster = xgb.train(
                fit_params, dfit, num_boost_round=config.model_params.num_boost_round
            )
            dval = xgb.DMatrix(x_val, feature_names=list(FEATURE_NAMES))
            val_raw = aux_booster.predict(dval)
            val_probs = calibrator.predict_proba(val_raw)
            threshold = fit_threshold_train_val_fbeta(y_val, val_probs, beta=config.beta)
            actual_method = config.threshold_method
    else:
        # Default fallback
        threshold = fit_threshold_train_f1(split.y_train, train_probs)
        actual_method = METHOD_TRAIN_F1_MAX

    # Evaluate train metrics
    train_metrics_dict = compute_metrics_suite(
        split.y_train, train_probs, threshold=threshold, beta=config.beta
    )
    metrics_map: dict[str, SplitMetrics] = {
        "train": SplitMetrics(
            n_samples=train_metrics_dict["n_samples"],
            n_positive=train_metrics_dict["n_positive"],
            prevalence=train_metrics_dict["prevalence"],
            threshold=threshold,
            beta=config.beta,
            precision=train_metrics_dict["precision"],
            recall=train_metrics_dict["recall"],
            f1=train_metrics_dict["f1"],
            fbeta=train_metrics_dict["fbeta"],
            auprc=train_metrics_dict["auprc"],
            brier=train_metrics_dict["brier"],
            confusion=ConfusionMatrix(**train_metrics_dict["confusion"]),
        )
    }

    # Evaluate val metrics if 2 classes present
    if len(np.unique(y_val)) >= 2:
        dval = xgb.DMatrix(x_val, feature_names=list(FEATURE_NAMES))
        val_probs = calibrator.predict_proba(booster.predict(dval))
        val_metrics_dict = compute_metrics_suite(
            y_val, val_probs, threshold=threshold, beta=config.beta
        )
        metrics_map["val"] = SplitMetrics(
            n_samples=val_metrics_dict["n_samples"],
            n_positive=val_metrics_dict["n_positive"],
            prevalence=val_metrics_dict["prevalence"],
            threshold=threshold,
            beta=config.beta,
            precision=val_metrics_dict["precision"],
            recall=val_metrics_dict["recall"],
            f1=val_metrics_dict["f1"],
            fbeta=val_metrics_dict["fbeta"],
            auprc=val_metrics_dict["auprc"],
            brier=val_metrics_dict["brier"],
            confusion=ConfusionMatrix(**val_metrics_dict["confusion"]),
        )

    # NOW score the locked held-out test split ONCE at the end
    dtest = xgb.DMatrix(split.x_test, feature_names=list(FEATURE_NAMES))
    raw_test_probs = booster.predict(dtest)
    test_probs = calibrator.predict_proba(raw_test_probs)

    test_metrics_dict = compute_metrics_suite(
        split.y_test, test_probs, threshold=threshold, beta=config.beta
    )
    test_confusion = ConfusionMatrix(**test_metrics_dict["confusion"])
    metrics_map["test"] = SplitMetrics(
        n_samples=test_metrics_dict["n_samples"],
        n_positive=test_metrics_dict["n_positive"],
        prevalence=test_metrics_dict["prevalence"],
        threshold=threshold,
        beta=config.beta,
        precision=test_metrics_dict["precision"],
        recall=test_metrics_dict["recall"],
        f1=test_metrics_dict["f1"],
        fbeta=test_metrics_dict["fbeta"],
        auprc=test_metrics_dict["auprc"],
        brier=test_metrics_dict["brier"],
        confusion=test_confusion,
    )

    # Write isolated model bundle
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = ModelBundleManifest(
        bundle_id=f"study-{config.study_id}-{config.run_id}",
        model_version="0.1.0-experiment",
        bundle_kind="option_b",
        feature_names=list(FEATURE_NAMES),
        feature_dtypes={name: "float" for name in FEATURE_NAMES},
        score_kind="proba_high_risk",
        score_threshold=threshold,
        threshold_fitting=actual_method,
        vol_veto_enabled=False,
        vol_veto_threshold=None,
        policy_version="v1",
        label_definition="fwd_return_5d < -0.03",
        label_window=LabelWindow(
            start="first_completed_session_close_at_or_after_event_session",
            end="close_5_trading_sessions_later",
        ),
        train_window=TrainWindow(start=split.train_start, end=split.train_end),
        dataset_hash=actual_hash,
        dataset_source=str(parquet_path),
        metrics={
            "test_precision": test_metrics_dict["precision"],
            "test_recall": test_metrics_dict["recall"],
            "test_f1": test_metrics_dict["f1"],
            "test_fbeta": test_metrics_dict["fbeta"],
            "test_auprc": test_metrics_dict["auprc"],
            "test_brier": test_metrics_dict["brier"],
            "seed": config.seed,
            "threshold_method": actual_method,
            "calibration_method": config.calibration_method,
        },
        library_versions={
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
            "python": sys.version.split()[0],
        },
        created_at=datetime.now(UTC),
        model_filename="model.json",
    )
    atomic_write_bundle(bundle_dir, booster, manifest)

    schema_version = None
    walk_forward_block = None
    economic_block = None
    if walk_forward != "off" or economic != "off":
        from alphaguard.ml.study_phaseb import attach_phase_b

        try:
            schema_version, walk_forward_block, economic_block = attach_phase_b(
                df=df,
                config=config,
                y_test=split.y_test,
                test_probs=test_probs,
                test_threshold=threshold,
                walk_forward=walk_forward,
                economic=economic,
                cost_fp=cost_fp,
                cost_fn=cost_fn,
                embargo_rows=embargo_rows,
            )
        except Exception as exc:
            logger.exception("phase B block failed")
            phase_reason = f"phase B failed: {exc}"
            aborted_experiment = True
            abort_reason = (
                phase_reason if not abort_reason else f"{abort_reason}; {phase_reason}"
            )

    wall_time = time.time() - start_time
    return RunRecord(
        run_id=config.run_id,
        study_id=config.study_id,
        git_sha=git_sha,
        dataset_hash=actual_hash,
        config_hash=config_hash,
        seed=config.seed,
        threshold_method=actual_method,
        calibration_method=config.calibration_method,
        split_policy=config.split_policy,
        score_threshold=threshold,
        wall_time_s=round(wall_time, 3),
        aborted=aborted_experiment,
        abort_reason=abort_reason,
        bundle_dir=str(bundle_dir),
        metrics=metrics_map,
        confusion=test_confusion,
        n_positive_train=n_pos_train,
        n_positive_val=n_pos_val,
        n_positive_test=int(split.y_test.sum()),
        config=config,
        schema_version=schema_version,
        walk_forward=walk_forward_block,
        economic=economic_block,
    )
