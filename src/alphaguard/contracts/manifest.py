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


class ModelBundleManifest(BaseModel):
    """Loadable gate artifact metadata — not a lone score string."""

    bundle_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    bundle_kind: BundleKind
    feature_names: list[str] = Field(min_length=1)
    feature_dtypes: dict[str, str] = Field(default_factory=dict)
    score_kind: ScoreKind = "proba_high_risk"
    score_threshold: float = Field(ge=0.0, le=1.0)
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
