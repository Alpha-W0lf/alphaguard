"""Model bundle manifest (ARCHITECTURE §7.6)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

BundleKind = Literal["fixture", "option_b"]
ScoreKind = Literal["proba_high_risk"]


class LabelWindow(BaseModel):
    start: str
    end: str


class TrainWindow(BaseModel):
    start: str
    end: str


class PlattCalibration(BaseModel):
    """Platt map applied to the raw booster output: sigmoid(coef * logit(p) + intercept).

    Fit on held-out rows that are never the locked test (`fit_on` says which).
    """

    method: Literal["platt"] = "platt"
    coef: float
    intercept: float
    fit_on: str = Field(min_length=1)
    n_fit_rows: int = Field(ge=1)


class ModelBundleManifest(BaseModel):
    """Loadable gate artifact metadata — not a lone score string."""

    bundle_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    bundle_kind: BundleKind
    feature_names: list[str] = Field(min_length=1)
    feature_dtypes: dict[str, str] = Field(default_factory=dict)
    score_kind: ScoreKind = "proba_high_risk"
    score_threshold: float = Field(ge=0.0, le=1.0)  # on the calibrated score when calibrated
    # None only for bundles written before calibration shipped; the gate warns on load.
    calibration: PlattCalibration | None = None
    threshold_fitting: str = "train_f1_max"
    vol_veto_enabled: bool = False
    vol_veto_threshold: float | None = None
    policy_version: str = "v1"
    label_definition: str = "fwd_return_5d < -0.03"
    label_window: LabelWindow
    train_window: TrainWindow
    dataset_hash: str
    dataset_source: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    library_versions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    model_filename: str = "model.json"
