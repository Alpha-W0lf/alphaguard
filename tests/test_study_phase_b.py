"""Phase B walk-forward + economic stub. Floors and the off-mode artifact stay put."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_economic import (
    RULES_SPEC,
    derive_rules_alerts,
    economic_split,
    rules_fn_hash,
)
from alphaguard.ml.study_executor import execute_run
from alphaguard.ml.study_phaseb import phase_c_trigger, promote_phaseb, summarize_phaseb
from alphaguard.ml.study_phaseb_cli import config_for_seed, main
from alphaguard.ml.study_promotion import evaluate_study_promotion
from alphaguard.ml.study_registry import dump_run_record
from alphaguard.ml.study_schema import (
    ConfusionMatrix,
    EconomicBlock,
    ModelHyperparams,
    PromotionConfig,
    RunConfig,
    RunRecord,
    SplitMetrics,
    WalkForwardAggregate,
    WalkForwardBlock,
    WalkForwardFoldMetrics,
)
from alphaguard.ml.study_walkforward import expanding4_folds, resolve_embargo_rows
from alphaguard.ml.train_option_b import dataset_hash

LEGACY_RUN_KEYS = (
    "run_id",
    "study_id",
    "git_sha",
    "dataset_hash",
    "config_hash",
    "seed",
    "threshold_method",
    "calibration_method",
    "split_policy",
    "score_threshold",
    "wall_time_s",
    "stage",
    "aborted",
    "abort_reason",
    "bundle_dir",
    "metrics",
    "confusion",
    "n_positive_train",
    "n_positive_val",
    "n_positive_test",
    "created_at",
    "config",
)

_GO_ASSIGN = re.compile(
    r"""(?i)(promotion_decision|decision)\s*=\s*['\"](?:go|model quality go)['\"]"""
)


def _synthetic_frame(n: int = 180, seed: int = 0) -> pd.DataFrame:
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


def _write_parquet(tmp_path: Path, n: int = 180) -> tuple[Path, str]:
    df = _synthetic_frame(n)
    parquet = tmp_path / "events.parquet"
    df.to_parquet(parquet)
    x_all = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y_all = df["label_high_risk"].to_numpy(dtype=int)
    return parquet, dataset_hash(x_all, y_all)


def _run_config(parquet: Path, digest: str, *, rounds: int = 5) -> RunConfig:
    return RunConfig(
        study_id="phaseb_test",
        run_id="run_phaseb",
        seed=0,
        dataset_path=str(parquet),
        dataset_hash=digest,
        threshold_method="train_f1_max",
        calibration_method="none",
        model_params=ModelHyperparams(max_depth=2, eta=0.1, num_boost_round=rounds),
    )


def _stable(record: RunRecord) -> dict:
    data = dump_run_record(record)
    data["wall_time_s"] = 0.0
    data["created_at"] = "fixed"
    data["git_sha"] = "fixed"
    data["bundle_dir"] = "fixed"
    return data


def _mock_run(run_id: str, seed: int, f1: float, precision: float, auprc: float) -> RunRecord:
    cfg = RunConfig(
        study_id="mock_study",
        run_id=run_id,
        seed=seed,
        dataset_path="mock.parquet",
        dataset_hash="mockhash",
        threshold_method="train_f1_max",
    )
    conf = ConfusionMatrix(tp=10, fp=5, tn=70, fn=5)
    test_m = SplitMetrics(
        n_samples=90,
        n_positive=15,
        prevalence=15 / 90,
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
        git_sha="abc",
        dataset_hash="mockhash",
        config_hash=cfg.compute_config_hash(),
        seed=seed,
        threshold_method="train_f1_max",
        score_threshold=0.5,
        wall_time_s=1.0,
        bundle_dir="bundle",
        metrics={"test": test_m},
        confusion=conf,
        n_positive_train=40,
        n_positive_test=15,
        config=cfg,
    )


def _toy_walk_forward() -> WalkForwardBlock:
    fold = WalkForwardFoldMetrics(
        fold=0,
        n_rows=10,
        positive_rate=0.2,
        precision=0.4,
        recall=0.5,
        f1=0.44,
        auprc=0.3,
        threshold=0.5,
        train_start=0,
        train_end=20,
        val_start=25,
        val_end=35,
    )
    return WalkForwardBlock(
        embargo_rows=5,
        embargo_source="label_horizon",
        n_dev=80,
        locked_test_start=80,
        folds=[fold],
        aggregate=WalkForwardAggregate(
            mean={"f1": 0.44},
            min={"f1": 0.44},
            std={"f1": 0.0},
        ),
    )


def test_expanding4_time_order_embargo_and_locked_test_disjoint() -> None:
    folds, n_dev, source = expanding4_folds(100, embargo_rows=5)
    assert source == "explicit"
    assert n_dev == 80
    locked = set(range(n_dev, 100))
    seen_val: set[int] = set()
    prev_train_end = -1
    for fold in folds:
        train = set(range(fold.train_start, fold.train_end))
        val = set(range(fold.val_start, fold.val_end))
        embargo = set(range(fold.train_end, fold.val_start))
        assert train.isdisjoint(val)
        assert train.isdisjoint(embargo)
        assert val.isdisjoint(embargo)
        assert len(embargo) == 5
        assert fold.train_end <= fold.val_start
        assert fold.train_end > prev_train_end
        prev_train_end = fold.train_end
        assert val.isdisjoint(locked)
        assert train.isdisjoint(locked)
        assert seen_val.isdisjoint(val)
        seen_val |= val
    assert seen_val.isdisjoint(locked)
    assert folds[-1].val_end == n_dev


def test_embargo_defaults_and_log(caplog) -> None:
    rows, source = resolve_embargo_rows(1000, None)
    assert (rows, source) == (5, "label_horizon")
    pct, pct_source = resolve_embargo_rows(1000, None, horizon_rows=None)
    assert (pct, pct_source) == (10, "dev_rows_1pct")
    with caplog.at_level(logging.INFO):
        expanding4_folds(200)
    assert "embargo_rows=5" in caplog.text
    assert "label_horizon" in caplog.text


def test_rules_baseline_is_prior_downside_not_saturated_vol() -> None:
    df = pd.DataFrame(
        {
            "volatility_20d": [0.30, 0.30, 0.30, 0.30],
            "return_5d_prior": [-0.04, -0.01, 0.02, -0.05],
        }
    )
    alerts, spec, digest = derive_rules_alerts(df)
    assert spec == "return_5d_prior<-0.03"
    assert digest == rules_fn_hash(spec)
    assert alerts.tolist() == [True, False, False, True]


def test_economic_stub_matches_hand_computation() -> None:
    y = np.array([1, 0, 1, 0, 0, 1, 0, 0])
    scores = np.array([0.9, 0.8, 0.2, 0.7, 0.1, 0.6, 0.4, 0.3])
    rules = np.array([1, 1, 0, 0, 0, 1, 0, 0], dtype=bool)
    block = economic_split(y, scores, rules, 0.5, cost_fp=1.0, cost_fn=10.0)
    assert block.rules_alerts == 3
    assert block.model_alerts_at_threshold == 4
    assert block.precision_at_rules_budget_model == 1 / 3
    assert block.recall_at_rules_budget_model == 1 / 3
    assert block.precision_at_rules_budget_rules == 2 / 3
    assert block.recall_at_rules_budget_rules == 2 / 3
    assert block.incremental_tp == 0
    assert block.rules_only_tp == 1
    assert block.stub_cost_model_at_threshold == 12
    assert block.stub_cost_model_at_budget == 22
    assert block.stub_cost_rules == 11
    shadow = block.shadow_agreement
    assert shadow.model_alert_rules_alert == 2
    assert shadow.model_alert_rules_quiet == 1
    assert shadow.model_quiet_rules_alert == 1
    assert shadow.model_quiet_rules_quiet == 4
    EconomicBlock.model_validate(
        {
            "label": "stub",
            "cost_fp": 1,
            "cost_fn": 10,
            "rules_spec": RULES_SPEC,
            "rules_fn_hash": rules_fn_hash(RULES_SPEC),
            "rules_mask_hash": "abc",
            "folds": [],
            "locked_test": block.model_dump(),
        }
    )


def test_walk_forward_off_byte_identical_to_legacy_keys(tmp_path: Path) -> None:
    parquet, digest = _write_parquet(tmp_path, n=80)
    config = _run_config(parquet, digest, rounds=8)
    default = execute_run(config, tmp_path / "bundle_default")
    explicit = execute_run(
        config,
        tmp_path / "bundle_off",
        walk_forward="off",
        economic="off",
    )
    assert _stable(default) == _stable(explicit)
    payload = dump_run_record(default)
    assert tuple(payload) == LEGACY_RUN_KEYS
    assert "walk_forward" not in payload
    assert "economic" not in payload
    assert "schema_version" not in payload
    golden = json.dumps(payload, indent=2) + "\n"
    loaded = RunRecord.model_validate_json(golden)
    assert json.dumps(dump_run_record(loaded), indent=2) + "\n" == golden


def test_legacy_artifact_promotes_identically() -> None:
    primary = _mock_run("run_primary", 42, 0.40, 0.30, 0.20)
    extra = _mock_run("run_extra", 7, 0.36, 0.28, 0.19)
    promo = PromotionConfig(extra_seeds=[7])
    loaded_p = RunRecord.model_validate(dump_run_record(primary))
    loaded_e = RunRecord.model_validate(dump_run_record(extra))
    assert loaded_p.walk_forward is None
    assert loaded_p.schema_version is None
    live = evaluate_study_promotion([primary], [primary, extra], promo)
    old = evaluate_study_promotion([loaded_p], [loaded_p, loaded_e], promo)
    assert live[0] == old[0] == "candidate"
    assert live[1] == old[1]
    assert live[2] == old[2]
    assert live[5] == old[5]

    rich = primary.model_copy(
        update={"walk_forward": _toy_walk_forward(), "schema_version": "1.1"}
    )
    with_blocks = evaluate_study_promotion([rich], [rich, extra], promo)
    assert with_blocks[0] == live[0]
    assert with_blocks[1] == live[1]
    assert with_blocks[2] == live[2]
    assert "floors unchanged" in with_blocks[5]
    assert with_blocks[0] in ("candidate", "rejected", "none")


def test_expanding4_run_disjoint_from_locked_test(tmp_path: Path) -> None:
    parquet, digest = _write_parquet(tmp_path, n=180)
    config = _run_config(parquet, digest)
    record = execute_run(
        config,
        tmp_path / "bundle",
        walk_forward="expanding4",
        economic="on",
        cost_fp=1.0,
        cost_fn=10.0,
    )
    assert not record.aborted, record.abort_reason
    assert record.schema_version == "1.1"
    assert record.walk_forward is not None
    assert record.economic is not None
    assert record.economic.label == "stub"
    assert record.economic.cost_fp == 1.0
    assert record.economic.cost_fn == 10.0
    assert record.threshold_method == "train_f1_max"
    n_dev = record.walk_forward.n_dev
    locked = set(range(n_dev, 180))
    wf_rows: set[int] = set()
    for fold in record.walk_forward.folds:
        val = set(range(fold.val_start, fold.val_end))
        train = set(range(fold.train_start, fold.train_end))
        assert fold.val_start - fold.train_end == record.walk_forward.embargo_rows
        assert train.isdisjoint(val)
        assert val.isdisjoint(locked)
        assert train.isdisjoint(locked)
        wf_rows |= val
    assert wf_rows.isdisjoint(locked)
    assert len(record.economic.folds) == 4
    assert record.economic.locked_test.n_rows == 180 - n_dev
    WalkForwardBlock.model_validate(record.walk_forward.model_dump())
    EconomicBlock.model_validate(record.economic.model_dump())


def test_phase_c_trigger_numbers() -> None:
    quiet = phase_c_trigger([[0.2, 0.2, 0.2, 0.2]], [[0.1, 0.1, 0.1, 0.12]], [0.2, 0.21])
    assert quiet["fired"] is False
    loud_rate = phase_c_trigger([[0.2, 0.2]], [[0.05, 0.2]], [0.2, 0.2])
    assert loud_rate["positive_rate_varies_gt_2x"] is True
    assert loud_rate["fired"] is True
    drift = phase_c_trigger([[0.1, 0.9], [0.1, 0.9]], [[0.2, 0.2], [0.2, 0.2]], [0.5, 0.5])
    assert drift["fold_std_gt_seed_std"] is True
    assert drift["seed_to_seed_std_f1"] == 0.0
    assert drift["fired"] is True


def test_promote_says_candidate_or_no_candidate_only(tmp_path: Path) -> None:
    run = _mock_run("run_low", 0, 0.10, 0.10, 0.10)
    out = tmp_path / "seed0"
    out.mkdir()
    (out / "run.json").write_text(
        json.dumps(dump_run_record(run), indent=2) + "\n", encoding="utf-8"
    )
    text = promote_phaseb(tmp_path)
    assert text.startswith("no candidate\n")
    assert "Model Quality Go" not in text
    summary = summarize_phaseb(tmp_path)
    assert "Per-seed × per-fold" in summary
    assert "Locked-test floors" in summary
    assert "fired:" in summary
    assert "Model Quality Go" not in summary


def test_no_code_path_writes_a_go_claim() -> None:
    root = Path(__file__).resolve().parents[1]
    roots = list((root / "src/alphaguard/ml").glob("study_*.py"))
    roots.append(root / "scripts/run_phase_b.py")
    for path in roots:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert _GO_ASSIGN.search(line) is None, f"{path}:{lineno}: {line}"


def test_phaseb_cli_uses_train_f1_max_and_freeze(tmp_path: Path) -> None:
    parquet, digest = _write_parquet(tmp_path, n=180)
    yaml_path = tmp_path / "study.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "study_id: phaseb_cli",
                "dataset_path: " + str(parquet),
                "dataset_hash: " + digest,
                "seeds: [7, 123]",
                "threshold_methods: [train_val_fbeta_0.5]",
                "betas: [1.0]",
                "calibration_methods: [none]",
                "max_depths: [2]",
                "etas: [0.1]",
                "num_boost_rounds: [5]",
                "scale_pos_weights: [2]",
                "train_frac: 0.8",
                "val_frac: 0.2",
            ]
        ),
        encoding="utf-8",
    )
    cfg = config_for_seed(yaml_path, seed=3, freeze=digest[:8])
    assert cfg.threshold_method == "train_f1_max"
    assert cfg.seed == 3
    assert cfg.model_params.scale_pos_weight == 2
    assert cfg.calibration_method == "none"
    out = tmp_path / "seed3"
    code = main(
        [
            "run",
            "--config",
            str(yaml_path),
            "--freeze",
            digest[:8],
            "--seed",
            "3",
            "--walk-forward",
            "expanding4",
            "--economic",
            "on",
            "--cost-fp",
            "1",
            "--cost-fn",
            "10",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    payload = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1"
    assert payload["threshold_method"] == "train_f1_max"
    assert payload["dataset_hash"] == digest
    assert payload["walk_forward"]["mode"] == "expanding4"
    assert payload["economic"]["label"] == "stub"
    assert "walk_forward" in payload and payload["git_sha"]
