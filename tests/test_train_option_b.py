"""Guide 05b — Option B train unit tests (synthetic; no live parquet required)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.gate import DownsideRiskGate, GateLoadError
from alphaguard.ml.train_eval import fit_threshold_train_f1
from alphaguard.ml.train_hpo import run_hpo
from alphaguard.ml.train_option_b import (
    TrainError,
    load_training_frame,
    time_ordered_split,
    train_option_b,
)
from alphaguard.ml.train_option_b_errors import TrainError as TrainErrorAlias

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_BUNDLE = ROOT / "data" / "fixtures" / "model_bundle_fixture"


def _synthetic_frame(n: int = 120, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    times = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    x = rng.normal(size=(n, len(FEATURE_NAMES)))
    # Mild signal so HPO/threshold are defined
    logits = 1.2 * x[:, 1] - 0.8 * x[:, 2] + 0.5 * x[:, 0]
    y = (logits > 0).astype(int)
    # Ensure both classes present in early and late windows
    y[:20] = [0, 1] * 10
    y[-20:] = [1, 0] * 10
    data = {name: x[:, i] for i, name in enumerate(FEATURE_NAMES)}
    data["label_high_risk"] = y
    data["published_at"] = times
    return pd.DataFrame(data)


def test_time_ordered_split_no_shuffle(tmp_path: Path) -> None:
    path = tmp_path / "events.parquet"
    df = _synthetic_frame()
    # Intentionally unsorted
    shuffled = df.sample(frac=1.0, random_state=1).reset_index(drop=True)
    shuffled.to_parquet(path)
    loaded = load_training_frame(path)
    assert loaded["published_at"].is_monotonic_increasing
    split = time_ordered_split(loaded)
    assert len(split.x_train) == 96
    assert len(split.x_test) == 24
    # Train window is earliest 80%
    assert split.train_start == str(loaded["published_at"].iloc[0])
    assert split.train_end == str(loaded["published_at"].iloc[95])


def test_nan_features_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "bad.parquet"
    df = _synthetic_frame(40)
    df.loc[3, "finbert_sentiment"] = np.nan
    df.to_parquet(path)
    with pytest.raises(TrainError, match="NaN"):
        load_training_frame(path)


def test_hpo_uses_only_train_indices() -> None:
    df = _synthetic_frame(160)
    split = time_ordered_split(df)
    n_pos = int(split.y_train.sum())
    n_neg = len(split.y_train) - n_pos
    spw = n_neg / n_pos
    # HPO API accepts only train matrices — test partition is never passed in.
    hpo = run_hpo(split.x_train, split.y_train, spw)
    assert hpo["method"] == "timeseries_split_grid"
    assert hpo["candidates_evaluated"] == 8
    assert "fold_logloss" in hpo
    assert len(hpo["fold_logloss"]) == 3
    assert len(split.x_train) == 128
    assert len(split.x_test) == 32


def test_threshold_train_only() -> None:
    y = np.array([0, 0, 1, 1, 0, 1, 0, 1], dtype=int)
    probs = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.15, 0.85])
    t = fit_threshold_train_f1(y, probs)
    assert 0.05 <= t <= 0.95


def test_train_writes_option_b_bundle(tmp_path: Path) -> None:
    parquet = tmp_path / "events.parquet"
    bundle = tmp_path / "bundle"
    runs = tmp_path / "runs"
    _synthetic_frame(160).to_parquet(parquet)
    manifest = train_option_b(parquet=parquet, bundle_dir=bundle, runs_dir=runs)
    assert manifest.bundle_kind == "option_b"
    assert list(manifest.feature_names) == list(FEATURE_NAMES)
    assert (bundle / "manifest.json").exists()
    assert (bundle / "model.json").exists()
    raw = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert raw["metrics"]["hpo"]["method"] == "timeseries_split_grid"
    assert raw["metrics"]["hyperparam_search"] == "timeseries_split_grid_05b"
    assert list(runs.glob("option_b_train_*.json"))
    gate = DownsideRiskGate(bundle)
    assert gate.manifest.bundle_kind == "option_b"


def test_require_bundle_kind_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    if not (FIXTURE_BUNDLE / "manifest.json").exists():
        pytest.skip("fixture bundle missing")
    monkeypatch.setenv("ALPHAGUARD_REQUIRE_BUNDLE_KIND", "option_b")
    with pytest.raises(GateLoadError, match="bundle_kind mismatch"):
        DownsideRiskGate(FIXTURE_BUNDLE)
    monkeypatch.delenv("ALPHAGUARD_REQUIRE_BUNDLE_KIND", raising=False)
    # Default load still works
    gate = DownsideRiskGate(FIXTURE_BUNDLE)
    assert gate.manifest.bundle_kind == "fixture"


def test_train_error_alias_exported() -> None:
    assert TrainError is TrainErrorAlias
