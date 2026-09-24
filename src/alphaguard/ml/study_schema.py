"""Contracts and schemas for MLOps experiment harness and run registry (JH-63.2)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from alphaguard.ml.study_calibration import CalibrationMethod

PromotionStatus = Literal["none", "candidate", "rejected"]


class PromotionFloors(BaseModel):
    """Locked floor criteria for candidate promotion (JH-AG-93.1)."""

    f1: float = 0.30
    precision: float = 0.25
    auprc: float = 0.18


class PromotionConfig(BaseModel):
    """Configuration for automatic multi-seed promotion gate (JH-AG-93.1)."""

    enabled: bool = True
    shortlist_top_k: int = 3
    extra_seeds: list[int] = Field(default_factory=lambda: [7, 123])
    floors: PromotionFloors = Field(default_factory=PromotionFloors)
    sort_by: str = "test_f1"  # primary sort key; ties broken by test_p, test_auprc, run_id


class ModelHyperparams(BaseModel):
    max_depth: int = 2
    eta: float = 0.1
    num_boost_round: int = 40
    scale_pos_weight: float | None = None  # None means auto (n_neg / n_pos)
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_lambda: float = 1.0


class RunConfig(BaseModel):
    """Canonical configuration for a single matrix cell."""

    study_id: str
    run_id: str
    seed: int = 42
    dataset_path: str
    dataset_hash: str
    threshold_method: str = "train_f1_max"  # e.g. "train_f1_max", "train_val_fbeta_0.5"
    beta: float = 0.5
    calibration_method: CalibrationMethod = "none"
    model_params: ModelHyperparams = Field(default_factory=ModelHyperparams)
    split_policy: str = "nested_time_aware_v1"
    train_frac: float = 0.8
    val_frac: float = 0.2

    def canonical_dict(self) -> dict[str, Any]:
        """Deterministic dictionary for configuration hashing."""
        return {
            "study_id": self.study_id,
            "seed": self.seed,
            "dataset_path": self.dataset_path,
            "dataset_hash": self.dataset_hash,
            "threshold_method": self.threshold_method,
            "beta": round(self.beta, 4),
            "calibration_method": self.calibration_method,
            "model_params": self.model_params.model_dump(),
            "split_policy": self.split_policy,
            "train_frac": round(self.train_frac, 4),
            "val_frac": round(self.val_frac, 4),
        }

    def compute_config_hash(self) -> str:
        """SHA-256 fingerprint of canonicalized configuration."""
        raw = json.dumps(self.canonical_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]


class ConfusionMatrix(BaseModel):
    tp: int
    fp: int
    tn: int
    fn: int


class SplitMetrics(BaseModel):
    n_samples: int
    n_positive: int
    prevalence: float
    threshold: float
    beta: float = 0.5
    precision: float
    recall: float
    f1: float
    fbeta: float
    auprc: float
    brier: float
    confusion: ConfusionMatrix


class RunRecord(BaseModel):
    """Child run record persisted to artifacts/runs/studies/<study_id>/runs/<run_id>.json."""

    run_id: str
    study_id: str
    git_sha: str
    dataset_hash: str
    config_hash: str
    seed: int
    threshold_method: str
    calibration_method: str = "none"
    split_policy: str = "nested_time_aware_v1"
    score_threshold: float
    wall_time_s: float
    stage: str = "primary"  # "primary" or "extra_seed"
    aborted: bool = False
    abort_reason: str | None = None
    bundle_dir: str
    metrics: dict[str, SplitMetrics] = Field(default_factory=dict)  # "train", "val", "test"
    confusion: ConfusionMatrix | None = None  # on locked test
    n_positive_train: int = 0
    n_positive_val: int | None = None
    n_positive_test: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    config: RunConfig


class ParentStudyRecord(BaseModel):
    """Parent study record persisted to artifacts/runs/studies/<study_id>/study.json."""

    study_id: str
    description: str = ""
    git_sha: str
    dataset_hash: str
    dataset_path: str
    matrix_source_path: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    total_runs: int = 0
    completed_runs: int = 0
    aborted_runs: int = 0
    child_run_ids: list[str] = Field(default_factory=list)
    promotion_decision: PromotionStatus = "none"
    notes: str = ""
    seeds_cleared: list[int] = Field(default_factory=list)
    seeds_failed: list[int] = Field(default_factory=list)
    seed_metrics_summary: dict[str, Any] = Field(default_factory=dict)
    promotion_rollup: dict[str, Any] | None = None


class StudyMatrixConfig(BaseModel):
    """Definition of an experiment study matrix (from YAML or code)."""

    study_id: str
    description: str = ""
    dataset_path: str
    dataset_hash: str | None = None  # Optional in input; resolved or verified at runtime
    seeds: list[int] = Field(default_factory=lambda: [42])
    threshold_methods: list[str] = Field(default_factory=lambda: ["train_f1_max"])
    betas: list[float] = Field(default_factory=lambda: [0.5])
    calibration_methods: list[CalibrationMethod] = Field(default_factory=lambda: ["none"])
    max_depths: list[int] = Field(default_factory=lambda: [2])
    etas: list[float] = Field(default_factory=lambda: [0.1])
    num_boost_rounds: list[int] = Field(default_factory=lambda: [40])
    scale_pos_weights: list[float | None] = Field(default_factory=lambda: [None])
    split_policy: str = "nested_time_aware_v1"
    train_frac: float = 0.8
    val_frac: float = 0.2
    enable_mlflow: bool = False
    mlflow_tracking_uri: str = "artifacts/mlruns"
    promotion: PromotionConfig | None = None
