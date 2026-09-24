"""Tests for auto multi-seed promotion gate and study schema extensions (JH-AG-93.1).

Verifies:
1. Deterministic shortlist selection with stable tie-breaking and hparam deduplication.
2. Pure floor evaluation (F1 >= 0.30, Precision >= 0.25, AUPRC >= 0.18) with zero soft misses.
3. Multi-seed gate decision: all extra seeds pass -> 'candidate'; any fail -> 'rejected'.
4. Integration in run_study: auto-scheduling of extra seeds and parent study.json rollup.
5. Backward compatibility with historical/legacy study.json and run records (Matrix C style).
6. Compare table generation with Promotion Gate section and visible confusion/n+ test metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_compare import write_study_compare
from alphaguard.ml.study_promotion import (
    build_extra_seed_configs,
    compute_hparam_signature,
    evaluate_floors,
    evaluate_study_promotion,
    select_shortlist,
)
from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_runner import run_study
from alphaguard.ml.study_schema import (
    ConfusionMatrix,
    ModelHyperparams,
    PromotionConfig,
    PromotionFloors,
    RunConfig,
    RunRecord,
    SplitMetrics,
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


def _mock_run(
    run_id: str,
    seed: int,
    f1: float,
    precision: float,
    auprc: float,
    threshold_method: str = "train_f1_max",
    max_depth: int = 2,
    aborted: bool = False,
) -> RunRecord:
    cfg = RunConfig(
        study_id="mock_study",
        run_id=run_id,
        seed=seed,
        dataset_path="mock.parquet",
        dataset_hash="mockhash",
        threshold_method=threshold_method,
        model_params=ModelHyperparams(max_depth=max_depth),
    )
    conf = ConfusionMatrix(tp=10, fp=15, tn=70, fn=5)
    test_m = SplitMetrics(
        n_samples=100,
        n_positive=15,
        prevalence=0.15,
        threshold=0.5,
        precision=precision,
        recall=0.66,
        f1=f1,
        fbeta=f1,
        auprc=auprc,
        brier=0.15,
        confusion=conf,
    )
    return RunRecord(
        run_id=run_id,
        study_id="mock_study",
        git_sha="abcdef12",
        dataset_hash="mockhash",
        config_hash=cfg.compute_config_hash(),
        seed=seed,
        threshold_method=threshold_method,
        score_threshold=0.5,
        wall_time_s=1.0,
        aborted=aborted,
        bundle_dir="/tmp/mock_bundle",
        metrics={"test": test_m} if not aborted else {},
        confusion=conf if not aborted else None,
        n_positive_test=15,
        config=cfg,
    )


def test_evaluate_floors_pure_function() -> None:
    floors = PromotionFloors(f1=0.30, precision=0.25, auprc=0.18)

    # All pass
    passed, failed = evaluate_floors(0.35, 0.28, 0.20, floors)
    assert passed
    assert len(failed) == 0

    # Exact boundary pass
    passed_exact, failed_exact = evaluate_floors(0.30, 0.25, 0.18, floors)
    assert passed_exact
    assert len(failed_exact) == 0

    # Soft misses are NOT allowed - any single fail rejects
    p_fail, f_list = evaluate_floors(0.35, 0.2499, 0.20, floors)
    assert not p_fail
    assert any("precision" in f for f in f_list)

    f1_fail, f_list2 = evaluate_floors(0.2999, 0.30, 0.25, floors)
    assert not f1_fail
    assert any("f1" in f for f in f_list2)

    auprc_fail, f_list3 = evaluate_floors(0.40, 0.30, 0.1799, floors)
    assert not auprc_fail
    assert any("auprc" in f for f in f_list3)

    # All fail
    all_fail, f_list4 = evaluate_floors(0.10, 0.10, 0.10, floors)
    assert not all_fail
    assert len(f_list4) == 3


def test_shortlist_deterministic_ranking_and_deduplication() -> None:
    # 4 runs: r1 and r2 share hparams but different seeds, r3 has lower F1, r4 has highest F1
    r1 = _mock_run("run_001", seed=42, f1=0.35, precision=0.28, auprc=0.22, max_depth=2)
    r2 = _mock_run("run_002", seed=7, f1=0.34, precision=0.27, auprc=0.21, max_depth=2)
    r3 = _mock_run("run_003", seed=42, f1=0.25, precision=0.20, auprc=0.15, max_depth=3)
    r4 = _mock_run("run_004", seed=42, f1=0.40, precision=0.32, auprc=0.25, max_depth=4)
    r_aborted = _mock_run("run_005", seed=42, f1=0.99, precision=0.99, auprc=0.99, aborted=True)

    runs = [r1, r2, r3, r4, r_aborted]
    shortlist = select_shortlist(runs, top_k=2, sort_by="test_f1")

    # top_k=2:
    # r4 (f1=0.40) is rank 1.
    # r1 (f1=0.35) is rank 2.
    # r2 has same hparams as r1, so deduplicated.
    # r_aborted is excluded despite high metric stub.
    assert len(shortlist) == 2
    assert shortlist[0].run_id == "run_004"
    assert shortlist[1].run_id == "run_001"

    # Deterministic tie breaking on precision and auprc
    tie_a = _mock_run("run_tie_a", seed=42, f1=0.35, precision=0.30, auprc=0.20, max_depth=5)
    tie_b = _mock_run("run_tie_b", seed=42, f1=0.35, precision=0.28, auprc=0.25, max_depth=6)
    shortlist_tie = select_shortlist([tie_b, tie_a], top_k=1, sort_by="test_f1")
    # Equal F1=0.35, tie_a has precision=0.30 > tie_b precision=0.28
    assert shortlist_tie[0].run_id == "run_tie_a"


def test_build_extra_seed_configs_skips_existing() -> None:
    candidate = _mock_run("run_cand", seed=42, f1=0.35, precision=0.30, auprc=0.20)
    extra_seeds = [7, 123]

    # No existing extra seed runs
    new_cfgs = build_extra_seed_configs([candidate], extra_seeds, [candidate], "test_study")
    assert len(new_cfgs) == 2
    assert {c.seed for c in new_cfgs} == {7, 123}

    # If seed 7 already exists for this hparam
    existing_s7 = _mock_run("run_s7", seed=7, f1=0.33, precision=0.28, auprc=0.21)
    new_cfgs_partial = build_extra_seed_configs(
        [candidate], extra_seeds, [candidate, existing_s7], "test_study"
    )
    assert len(new_cfgs_partial) == 1
    assert new_cfgs_partial[0].seed == 123


def test_promotion_evaluation_candidate_when_all_pass() -> None:
    cand = _mock_run("run_p", seed=42, f1=0.35, precision=0.28, auprc=0.20)
    s7 = _mock_run("run_s7", seed=7, f1=0.32, precision=0.26, auprc=0.19)
    s123 = _mock_run("run_s123", seed=123, f1=0.31, precision=0.27, auprc=0.22)

    config = PromotionConfig(
        enabled=True,
        shortlist_top_k=1,
        extra_seeds=[7, 123],
        floors=PromotionFloors(f1=0.30, precision=0.25, auprc=0.18),
    )

    decision, cleared, failed, summary, rollup, notes = evaluate_study_promotion(
        [cand], [cand, s7, s123], config
    )

    assert decision == "candidate"
    assert set(cleared) == {42, 7, 123}
    assert len(failed) == 0
    assert "Human Model Quality Go review required" in notes
    assert rollup["winning_candidate_hash"] == compute_hparam_signature(cand.config)


def test_promotion_evaluation_rejected_when_any_extra_seed_fails() -> None:
    cand = _mock_run("run_p", seed=42, f1=0.35, precision=0.28, auprc=0.20)
    # seed 7 clears
    s7 = _mock_run("run_s7", seed=7, f1=0.32, precision=0.26, auprc=0.19)
    # seed 123 fails precision (matches historical go-gate failure pattern)
    s123 = _mock_run("run_s123", seed=123, f1=0.32, precision=0.2263, auprc=0.19)

    config = PromotionConfig(
        enabled=True,
        shortlist_top_k=1,
        extra_seeds=[7, 123],
        floors=PromotionFloors(f1=0.30, precision=0.25, auprc=0.18),
    )

    decision, cleared, failed, summary, rollup, notes = evaluate_study_promotion(
        [cand], [cand, s7, s123], config
    )

    assert decision == "rejected"
    assert 123 in failed
    assert rollup["winning_candidate_hash"] is None
    assert "rejected" in notes


def test_promotion_gate_disabled_returns_none() -> None:
    cand = _mock_run("run_p", seed=42, f1=0.35, precision=0.28, auprc=0.20)
    config = PromotionConfig(enabled=False)

    decision, cleared, failed, summary, rollup, notes = evaluate_study_promotion(
        [cand], [cand], config
    )
    assert decision == "none"
    assert len(cleared) == 0


def test_auto_multi_seed_end_to_end_in_runner(tmp_path: Path) -> None:
    """Test full run_study loop with promotion gate enabled."""
    parquet = tmp_path / "events.parquet"
    df = _synthetic_frame(120)
    df.to_parquet(parquet)

    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    d_hash = dataset_hash(x_all, y_all)

    matrix = StudyMatrixConfig(
        study_id="auto_promo_study",
        dataset_path=str(parquet),
        dataset_hash=d_hash,
        seeds=[42],
        threshold_methods=["train_f1_max"],
        max_depths=[2],
        num_boost_rounds=[10],
        promotion=PromotionConfig(
            enabled=True,
            shortlist_top_k=1,
            extra_seeds=[7, 123],
            floors=PromotionFloors(f1=0.30, precision=0.25, auprc=0.18),
        ),
    )

    artifacts_root = tmp_path / "artifacts" / "runs"
    parent, runs = run_study(matrix, registry_root=artifacts_root, max_workers=2)

    # 1 discovery run (seed 42) + 2 extra-seed runs (seeds 7, 123) = 3 total runs
    assert len(runs) == 3
    assert parent.total_runs == 3
    assert parent.completed_runs == 3
    assert parent.aborted_runs == 0
    assert parent.promotion_decision in ("candidate", "rejected")
    assert parent.promotion_rollup is not None

    # Verify extra seed runs are registered
    seeds_executed = {r.seed for r in runs}
    assert seeds_executed == {42, 7, 123}

    # Verify compare table includes Promotion Gate section
    study_dir = artifacts_root / "studies" / "auto_promo_study"
    md_path, csv_path = write_study_compare(study_dir)

    md_content = md_path.read_text(encoding="utf-8")
    assert "## Promotion Gate (JH-AG-93.1)" in md_content
    assert "Gate Decision:" in md_content
    assert "Target Floors:" in md_content
    assert "Notice:" in md_content


def test_backward_compatible_read_of_matrix_c_artifacts(tmp_path: Path) -> None:
    """Verify that existing Matrix C style study.json (without promotion fields) loads cleanly."""
    study_dir = tmp_path / "studies" / "jh63_matrix_c_8907"
    study_dir.mkdir(parents=True)

    legacy_json = {
        "study_id": "jh63_matrix_c_8907",
        "description": "Matrix C 8907 rows",
        "git_sha": "7974716",
        "dataset_hash": "534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3",
        "dataset_path": "data/derived/training_events.parquet",
        "total_runs": 96,
        "completed_runs": 96,
        "aborted_runs": 0,
        "child_run_ids": ["run_000", "run_001"],
        "promotion_decision": "none",
        "notes": "",
    }

    study_file = study_dir / "study.json"
    study_file.write_text(json.dumps(legacy_json, indent=2), encoding="utf-8")

    registry = StudyRegistry(tmp_path)
    loaded = registry.load_study("jh63_matrix_c_8907")

    assert loaded.study_id == "jh63_matrix_c_8907"
    assert loaded.promotion_decision == "none"
    assert loaded.seeds_cleared == []
    assert loaded.seeds_failed == []
    assert loaded.promotion_rollup is None
