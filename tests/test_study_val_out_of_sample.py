"""Validation metrics that rank the shortlist must be out-of-sample.

The final booster trains on all of train, including the last-20% val slice, so its
scores on that slice are in-sample. metrics["val"] must come from the auxiliary booster
that trained on the first 80% only; a run whose val slice has one class fails closed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.study_executor import execute_run
from alphaguard.ml.study_promotion import select_shortlist
from alphaguard.ml.study_schema import ModelHyperparams, RunConfig
from alphaguard.ml.train_eval import VAL_SINGLE_CLASS_REASON
from alphaguard.ml.train_option_b import dataset_hash


def _noisy_frame(n: int = 2000, seed: int = 0) -> pd.DataFrame:
    """One real signal (feature 1) plus 15% label noise: memorising train does not transfer."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, len(FEATURE_NAMES)))
    y = (x[:, 1] > 0.6).astype(int)
    flip = rng.random(n) < 0.15
    y[flip] = 1 - y[flip]
    data = {name: x[:, i] for i, name in enumerate(FEATURE_NAMES)}
    data["label_high_risk"] = y
    data["published_at"] = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame(data)


def _write(df: pd.DataFrame, tmp_path: Path) -> tuple[str, str]:
    path = tmp_path / "events.parquet"
    df.to_parquet(path)
    x = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y = df["label_high_risk"].to_numpy(dtype=int)
    return str(path), dataset_hash(x, y)


def _config(run_id: str, path: str, d_hash: str, params: ModelHyperparams, **kw) -> RunConfig:
    return RunConfig(
        study_id="oos",
        run_id=run_id,
        seed=42,
        dataset_path=path,
        dataset_hash=d_hash,
        threshold_method="train_f1_max",
        calibration_method=kw.pop("calibration_method", "none"),
        model_params=params,
        **kw,
    )


def test_config_that_only_overfits_train_cannot_top_the_shortlist(tmp_path: Path) -> None:
    path, d_hash = _write(_noisy_frame(), tmp_path)
    simple = _config("run_simple", path, d_hash, ModelHyperparams(max_depth=1, num_boost_round=30))
    overfit = _config(
        "run_overfit",
        path,
        d_hash,
        ModelHyperparams(
            max_depth=10, eta=0.5, num_boost_round=300, subsample=1.0, colsample_bytree=1.0,
            reg_lambda=0.0,
        ),
    )
    runs = [execute_run(c, tmp_path / c.run_id) for c in (simple, overfit)]
    assert not any(r.aborted for r in runs)
    by_id = {r.run_id: r for r in runs}

    # The overfit booster memorises train, but its val score is out-of-sample,
    # so the in-sample advantage does not reach the shortlist ranking.
    assert by_id["run_overfit"].metrics["train"].f1 > 0.95
    assert by_id["run_overfit"].metrics["val"].f1 < by_id["run_simple"].metrics["val"].f1
    assert select_shortlist(runs, top_k=1)[0].run_id == "run_simple"


def test_single_class_val_slice_fails_closed(tmp_path: Path) -> None:
    df = _noisy_frame(n=300)
    n_train = int(len(df) * 0.8)
    n_fit = int(n_train * 0.8)
    df.loc[n_fit : n_train - 1, "label_high_risk"] = 0  # val slice: one class
    path, d_hash = _write(df, tmp_path)

    record = execute_run(
        _config("run_one_class", path, d_hash, ModelHyperparams(), calibration_method="platt"),
        tmp_path / "bundle",
    )

    assert record.aborted
    assert VAL_SINGLE_CLASS_REASON in (record.abort_reason or "")
    assert not (tmp_path / "bundle" / "model.json").exists()
