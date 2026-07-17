"""Option B XGBoost train — nested time-aware HPO + train-only threshold (Guide 05b)."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.contracts.manifest import LabelWindow, ModelBundleManifest, TrainWindow
from alphaguard.ml.gate import write_manifest
from alphaguard.ml.train_eval import fit_threshold_train_f1, split_metrics
from alphaguard.ml.train_hpo import N_SPLITS, booster_params, run_hpo, train_booster
from alphaguard.ml.train_option_b_errors import TrainError

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PARQUET = REPO_ROOT / "data" / "derived" / "training_events.parquet"
DEFAULT_BUNDLE = REPO_ROOT / "data" / "derived" / "model_bundle_option_b"
DEFAULT_RUNS = REPO_ROOT / "artifacts" / "runs"
F1_GAP_WARN = 0.25

__all__ = [
    "DEFAULT_BUNDLE",
    "DEFAULT_PARQUET",
    "DEFAULT_RUNS",
    "TrainError",
    "train_option_b",
]


@dataclass(frozen=True)
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    train_start: str
    train_end: str


def load_training_frame(parquet: Path) -> pd.DataFrame:
    if not parquet.exists():
        raise TrainError(
            f"parquet missing: {parquet}. Regenerate via docs/TRAINING_DATA.md "
            "(scripts/build_training_events.py)."
        )
    df = pd.read_parquet(parquet)
    required = list(FEATURE_NAMES) + ["label_high_risk", "published_at"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise TrainError(f"parquet missing columns: {missing}")
    if df.empty:
        raise TrainError("parquet is empty")
    feat = df[list(FEATURE_NAMES)]
    if feat.isna().any().any() or df["label_high_risk"].isna().any():
        raise TrainError("NaN in FEATURE_NAMES or label_high_risk — fail closed")
    out = df.copy()
    out["published_at"] = pd.to_datetime(out["published_at"], utc=True)
    return out.sort_values("published_at", kind="mergesort").reset_index(drop=True)


def time_ordered_split(df: pd.DataFrame, train_frac: float = 0.8) -> SplitData:
    n = len(df)
    n_train = int(n * train_frac)
    if n_train < N_SPLITS + 1 or n - n_train < 1:
        raise TrainError(f"split too small: n={n}, n_train={n_train}")
    train = df.iloc[:n_train]
    test = df.iloc[n_train:]
    return SplitData(
        x_train=train[list(FEATURE_NAMES)].to_numpy(dtype=float),
        y_train=train["label_high_risk"].to_numpy(dtype=int),
        x_test=test[list(FEATURE_NAMES)].to_numpy(dtype=float),
        y_test=test["label_high_risk"].to_numpy(dtype=int),
        train_start=str(train["published_at"].iloc[0]),
        train_end=str(train["published_at"].iloc[-1]),
    )


def dataset_hash(x: np.ndarray, y: np.ndarray) -> str:
    return hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest()


def atomic_write_bundle(
    bundle_dir: Path,
    booster: xgb.Booster,
    manifest: ModelBundleManifest,
) -> None:
    bundle_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=bundle_dir.parent) as tmp:
        tmp_path = Path(tmp)
        booster.save_model(str(tmp_path / manifest.model_filename))
        write_manifest(tmp_path / "manifest.json", manifest)
        (tmp_path / "README.md").write_text(
            "# Option B model bundle\n\n"
            f"`bundle_kind=option_b` — trained downside-risk scorer (Guide 05b).\n"
            f"score_threshold={manifest.score_threshold:.4f} (train F1 max).\n"
            f"hyperparam_search={manifest.metrics.get('hyperparam_search')}\n"
            "Not a production risk model; lab-scale metrics only.\n"
            "Default smoke still uses the fixture bundle unless MODEL_BUNDLE_DIR points here.\n",
            encoding="utf-8",
        )
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)
        shutil.copytree(tmp_path, bundle_dir)


def write_run_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def train_option_b(
    parquet: Path = DEFAULT_PARQUET,
    bundle_dir: Path = DEFAULT_BUNDLE,
    runs_dir: Path = DEFAULT_RUNS,
) -> ModelBundleManifest:
    df = load_training_frame(parquet)
    split = time_ordered_split(df)
    n_pos = int(split.y_train.sum())
    n_neg = int(len(split.y_train) - n_pos)
    if n_pos == 0:
        raise TrainError("n_pos_train==0 — cannot compute scale_pos_weight")
    scale_pos_weight = float(n_neg) / float(n_pos)

    hpo = run_hpo(split.x_train, split.y_train, scale_pos_weight)
    winner = hpo["winner"]
    booster = train_booster(
        split.x_train,
        split.y_train,
        max_depth=winner["max_depth"],
        eta=winner["eta"],
        num_boost_round=winner["num_boost_round"],
        scale_pos_weight=scale_pos_weight,
    )
    dtrain = xgb.DMatrix(split.x_train, feature_names=list(FEATURE_NAMES))
    dtest = xgb.DMatrix(split.x_test, feature_names=list(FEATURE_NAMES))
    train_probs = booster.predict(dtrain)
    test_probs = booster.predict(dtest)
    threshold = fit_threshold_train_f1(split.y_train, train_probs)
    train_m = split_metrics(split.y_train, train_probs, threshold)
    test_m = split_metrics(split.y_test, test_probs, threshold)
    gap = abs(train_m["f1"] - test_m["f1"])
    if gap > F1_GAP_WARN:
        print(
            f"WARNING: large train/test F1 gap ({gap:.4f}) — possible overfit",
            file=sys.stderr,
        )

    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    xgb_params = booster_params(scale_pos_weight, winner["max_depth"], winner["eta"])
    xgb_params["num_boost_round"] = winner["num_boost_round"]

    metrics: dict[str, Any] = {
        "n_train": int(len(split.y_train)),
        "n_test": int(len(split.y_test)),
        "n_positive_train": n_pos,
        "n_positive_test": int(split.y_test.sum()),
        "score_threshold": threshold,
        "train_precision": train_m["precision"],
        "train_recall": train_m["recall"],
        "train_f1": train_m["f1"],
        "train_tp": train_m["tp"],
        "train_fp": train_m["fp"],
        "train_tn": train_m["tn"],
        "train_fn": train_m["fn"],
        "test_precision": test_m["precision"],
        "test_recall": test_m["recall"],
        "test_f1": test_m["f1"],
        "test_tp": test_m["tp"],
        "test_fp": test_m["fp"],
        "test_tn": test_m["tn"],
        "test_fn": test_m["fn"],
        "train_test_f1_gap": gap,
        "xgb_params": xgb_params,
        "scale_pos_weight": scale_pos_weight,
        "hpo": hpo,
        "hyperparam_search": "timeseries_split_grid_05b",
    }

    created = datetime.now(timezone.utc)
    manifest = ModelBundleManifest(
        bundle_id="option-b-downside-v1",
        model_version="0.1.0-option-b",
        bundle_kind="option_b",
        feature_names=list(FEATURE_NAMES),
        feature_dtypes={name: "float" for name in FEATURE_NAMES},
        score_kind="proba_high_risk",
        score_threshold=threshold,
        threshold_fitting="train_f1_max",
        vol_veto_enabled=False,
        vol_veto_threshold=None,
        policy_version="v1",
        label_definition="fwd_return_5d < -0.03",
        label_window=LabelWindow(
            start="first_completed_session_close_at_or_after_event_session",
            end="close_5_trading_sessions_later",
        ),
        train_window=TrainWindow(start=split.train_start, end=split.train_end),
        dataset_hash=dataset_hash(x_all, y_all),
        dataset_source=str(parquet),
        metrics=metrics,
        library_versions={
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
            "python": sys.version.split()[0],
        },
        created_at=created,
        model_filename="model.json",
    )
    atomic_write_bundle(bundle_dir, booster, manifest)
    stamp = created.strftime("%Y%m%dT%H%M%SZ")
    write_run_summary(
        runs_dir / f"option_b_train_{stamp}.json",
        {
            "created_at": created.isoformat(),
            "parquet": str(parquet),
            "bundle_dir": str(bundle_dir),
            "bundle_kind": "option_b",
            "score_threshold": threshold,
            "metrics": metrics,
            "winner": winner,
            "dataset_hash": manifest.dataset_hash,
        },
    )
    logger.info(
        "wrote Option B bundle to %s (test_f1=%.4f, threshold=%.4f)",
        bundle_dir,
        test_m["f1"],
        threshold,
    )
    return manifest
