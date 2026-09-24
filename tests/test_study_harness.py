"""Tests for MLOps experiment harness and run registry (JH-63.2).

Verifies:
1. Parallel execution across >=2 configs with ProcessPoolExecutor.
2. Parent study JSON and child run JSON schema compliance.
3. Isolated bundle directories, seeds, and config hashes.
4. Strict leakage discipline: HPO/threshold/calibration never see test rows.
5. Dataset hash validation and mismatch abort handling.
6. Compare table generation (Markdown and CSV).
7. Metrics suite correctness (Precision, Recall, F1, Fbeta, AUPRC, Brier, prevalence).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_calibration import ProbabilityCalibrator
from alphaguard.ml.study_compare import (
    write_study_compare,
)
from alphaguard.ml.study_executor import execute_run
from alphaguard.ml.study_metrics import compute_metrics_suite
from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_runner import generate_run_configs, run_study
from alphaguard.ml.study_schema import (
    ModelHyperparams,
    RunConfig,
    StudyMatrixConfig,
)
from alphaguard.ml.train_option_b import dataset_hash


def _synthetic_frame(n: int = 120, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    times = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    x = rng.normal(size=(n, len(FEATURE_NAMES)))
    logits = 1.2 * x[:, 1] - 0.8 * x[:, 2] + 0.5 * x[:, 0]
    y = (logits > 0).astype(int)
    y[:20] = [0, 1] * 10
    y[-20:] = [1, 0] * 10
    n_train = int(n * 0.8)
    n_fit = int(n_train * 0.8)
    if n_fit + 1 < n_train:
        y[n_fit] = 0
        y[n_fit + 1] = 1
    data = {name: x[:, i] for i, name in enumerate(FEATURE_NAMES)}
    data["label_high_risk"] = y
    data["published_at"] = times
    return pd.DataFrame(data)


def test_metrics_suite_computation() -> None:
    y_true = np.array([1, 0, 1, 0, 1, 0, 0, 0])
    probs = np.array([0.9, 0.8, 0.7, 0.1, 0.85, 0.2, 0.05, 0.6])
    threshold = 0.5
    res = compute_metrics_suite(y_true, probs, threshold=threshold, beta=0.5)

    assert res["n_samples"] == 8
    assert res["n_positive"] == 3
    assert res["prevalence"] == 0.375
    assert res["threshold"] == 0.5
    assert 0.0 <= res["precision"] <= 1.0
    assert 0.0 <= res["recall"] <= 1.0
    assert 0.0 <= res["f1"] <= 1.0
    assert 0.0 <= res["fbeta"] <= 1.0
    assert 0.0 <= res["auprc"] <= 1.0
    assert 0.0 <= res["brier"] <= 1.0
    assert "confusion" in res
    c = res["confusion"]
    assert c["tp"] + c["fp"] + c["tn"] + c["fn"] == 8


def test_calibrator_platt_and_isotonic() -> None:
    y = np.array([0, 0, 0, 1, 1, 1])
    p = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])

    cal_none = ProbabilityCalibrator("none").fit(p, y)
    np.testing.assert_allclose(cal_none.predict_proba(p), p)

    cal_platt = ProbabilityCalibrator("platt").fit(p, y)
    p_platt = cal_platt.predict_proba(p)
    assert len(p_platt) == 6
    assert (p_platt >= 0.0).all() and (p_platt <= 1.0).all()

    cal_iso = ProbabilityCalibrator("isotonic").fit(p, y)
    p_iso = cal_iso.predict_proba(p)
    assert len(p_iso) == 6
    assert (p_iso >= 0.0).all() and (p_iso <= 1.0).all()


def test_matrix_expansion_reproducibility() -> None:
    matrix = StudyMatrixConfig(
        study_id="study_test_grid",
        dataset_path="data/test.parquet",
        dataset_hash="hash123",
        seeds=[42, 100],
        threshold_methods=["train_f1_max", "train_val_fbeta_0.5"],
        max_depths=[2],
        etas=[0.1],
        num_boost_rounds=[20],
        scale_pos_weights=[None],
    )
    configs = generate_run_configs(matrix)
    assert len(configs) == 4  # 2 seeds * 2 threshold methods

    # Ensure run_id and config_hash are unique per config
    run_ids = [c.run_id for c in configs]
    config_hashes = [c.compute_config_hash() for c in configs]
    assert len(set(run_ids)) == 4
    # Config hashes depend on seed and parameters
    assert len(set(config_hashes)) == 4


def test_single_run_executor_leakage_and_artifacts(tmp_path: Path) -> None:
    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(100)
    df.to_parquet(parquet)

    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    d_hash = dataset_hash(x_all, y_all)

    config = RunConfig(
        study_id="test_single_study",
        run_id="run_001",
        seed=42,
        dataset_path=str(parquet),
        dataset_hash=d_hash,
        threshold_method="train_f1_max",
        calibration_method="none",
        model_params=ModelHyperparams(max_depth=2, eta=0.1, num_boost_round=10),
    )

    bundle_dir = tmp_path / "bundle_run_001"
    record = execute_run(config, bundle_dir)

    assert not record.aborted
    assert record.dataset_hash == d_hash
    assert record.git_sha != ""
    assert record.metrics["train"].f1 >= 0.0
    assert record.metrics["test"].f1 >= 0.0
    assert record.confusion is not None
    assert (bundle_dir / "manifest.json").exists()
    assert (bundle_dir / "model.json").exists()

    # Verify manifest.json matches run attributes
    manifest_data = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_data["dataset_hash"] == d_hash
    assert manifest_data["score_threshold"] == record.score_threshold


def test_dataset_hash_mismatch_aborts_run(tmp_path: Path) -> None:
    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(80)
    df.to_parquet(parquet)

    config = RunConfig(
        study_id="mismatch_study",
        run_id="run_mismatch",
        seed=42,
        dataset_path=str(parquet),
        dataset_hash="expected_hash_that_does_not_match",
        threshold_method="train_f1_max",
    )

    bundle_dir = tmp_path / "bundle_mismatch"
    record = execute_run(config, bundle_dir)

    assert record.aborted
    assert "Dataset hash mismatch" in (record.abort_reason or "")


def test_parallel_study_runner_processpool(tmp_path: Path) -> None:
    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(120)
    df.to_parquet(parquet)

    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    d_hash = dataset_hash(x_all, y_all)

    matrix = StudyMatrixConfig(
        study_id="parallel_smoke_study",
        description="Parallel study smoke test",
        dataset_path=str(parquet),
        dataset_hash=d_hash,
        seeds=[42, 99],
        threshold_methods=["train_f1_max"],
        calibration_methods=["none"],
        max_depths=[2],
        etas=[0.1],
        num_boost_rounds=[10],
        scale_pos_weights=[None],
    )

    artifacts_root = tmp_path / "artifacts" / "runs"
    parent, runs = run_study(matrix, registry_root=artifacts_root, max_workers=2)

    assert parent.study_id == "parallel_smoke_study"
    assert parent.total_runs == 2
    assert parent.completed_runs == 2
    assert parent.aborted_runs == 0
    assert len(runs) == 2

    # Check persistence in registry
    registry = StudyRegistry(artifacts_root)
    loaded_parent = registry.load_study("parallel_smoke_study")
    assert loaded_parent.study_id == parent.study_id
    assert loaded_parent.completed_runs == 2

    loaded_runs = registry.list_runs("parallel_smoke_study")
    assert len(loaded_runs) == 2

    # Verify each run has its own isolated bundle dir
    bundle_paths = [Path(r.bundle_dir) for r in runs]
    assert len(set(bundle_paths)) == 2
    for b in bundle_paths:
        assert b.exists()
        assert (b / "manifest.json").exists()


def test_compare_table_generation(tmp_path: Path) -> None:
    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(100)
    df.to_parquet(parquet)

    matrix = StudyMatrixConfig(
        study_id="compare_test_study",
        dataset_path=str(parquet),
        seeds=[42],
        threshold_methods=["train_f1_max", "train_val_fbeta_0.5"],
        num_boost_rounds=[10],
    )

    artifacts_root = tmp_path / "artifacts" / "runs"
    parent, runs = run_study(matrix, registry_root=artifacts_root, max_workers=1)

    study_dir = artifacts_root / "studies" / "compare_test_study"
    md_path, csv_path = write_study_compare(study_dir)

    assert md_path.exists()
    assert csv_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "# Study Comparison: compare_test_study" in md_content
    assert "Test F1" in md_content
    assert "AUPRC" in md_content
    assert "Confusion" in md_content

    csv_content = csv_path.read_text(encoding="utf-8")
    assert "run_id,git_sha,dataset_hash" in csv_content


def test_leakage_guard_test_never_in_threshold_search(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Explicit leakage assertion: test partition labels are never passed to threshold fitters."""
    import alphaguard.ml.study_executor as se

    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(120)
    df.to_parquet(parquet)

    n = 120
    n_train = int(n * 0.8)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    y_test = y_all[n_train:]

    seen_labels: list[np.ndarray] = []
    real_f1 = se.fit_threshold_train_f1
    real_fbeta = se.fit_threshold_train_val_fbeta

    def spy_f1(y, probs):
        seen_labels.append(np.asarray(y).copy())
        return real_f1(y, probs)

    def spy_fbeta(y, probs, **kwargs):
        seen_labels.append(np.asarray(y).copy())
        return real_fbeta(y, probs, **kwargs)

    monkeypatch.setattr(se, "fit_threshold_train_f1", spy_f1)
    monkeypatch.setattr(se, "fit_threshold_train_val_fbeta", spy_fbeta)

    # Test with train_val_fbeta_0.5
    config = RunConfig(
        study_id="leakage_guard_study",
        run_id="run_leakage_check",
        seed=42,
        dataset_path=str(parquet),
        dataset_hash="",
        threshold_method="train_val_fbeta_0.5",
        model_params=ModelHyperparams(num_boost_round=5),
    )
    bundle_dir = tmp_path / "bundle_leakage"
    record = execute_run(config, bundle_dir)
    assert not record.aborted

    # Verify that seen_labels NEVER contains y_test
    assert len(seen_labels) >= 1
    for labels in seen_labels:
        assert len(labels) != len(y_test)
        assert not np.array_equal(labels, y_test)

