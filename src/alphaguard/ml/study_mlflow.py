"""Optional local MLflow file store logging for experiment harness (JH-63.2).

OFF by default. File store only (artifacts/mlruns); no Databricks, no paid cloud tracking.
"""

from __future__ import annotations

import logging
from pathlib import Path

from alphaguard.ml.study_schema import RunRecord

logger = logging.getLogger(__name__)


def log_run_to_mlflow(
    record: RunRecord,
    tracking_uri: str | Path = "artifacts/mlruns",
) -> None:
    """Log a completed RunRecord to a local MLflow file store if mlflow is installed."""
    try:
        import mlflow
    except ImportError:
        logger.debug("mlflow not installed; skipping mlflow logging")
        return

    uri_str = str(Path(tracking_uri).resolve())
    mlflow.set_tracking_uri(f"file://{uri_str}")
    mlflow.set_experiment(record.study_id)

    with mlflow.start_run(run_name=record.run_id):
        # Tags
        mlflow.set_tags(
            {
                "git_sha": record.git_sha,
                "dataset_hash": record.dataset_hash,
                "config_hash": record.config_hash,
                "split_policy": record.split_policy,
                "threshold_method": record.threshold_method,
                "calibration_method": record.calibration_method,
                "aborted": str(record.aborted),
            }
        )

        # Params
        mlflow.log_params(
            {
                "seed": record.seed,
                "score_threshold": record.score_threshold,
                "max_depth": record.config.model_params.max_depth,
                "eta": record.config.model_params.eta,
                "num_boost_round": record.config.model_params.num_boost_round,
                "scale_pos_weight": str(record.config.model_params.scale_pos_weight),
            }
        )

        # Metrics
        mlflow.log_metric("wall_time_s", record.wall_time_s)
        for split_name, split_m in record.metrics.items():
            mlflow.log_metrics(
                {
                    f"{split_name}_precision": split_m.precision,
                    f"{split_name}_recall": split_m.recall,
                    f"{split_name}_f1": split_m.f1,
                    f"{split_name}_fbeta": split_m.fbeta,
                    f"{split_name}_auprc": split_m.auprc,
                    f"{split_name}_brier": split_m.brier,
                    f"{split_name}_prevalence": split_m.prevalence,
                }
            )

        if record.confusion is not None:
            mlflow.log_metrics(
                {
                    "test_tp": record.confusion.tp,
                    "test_fp": record.confusion.fp,
                    "test_tn": record.confusion.tn,
                    "test_fn": record.confusion.fn,
                }
            )
