"""Build a tiny fixture XGBoost bundle (bundle_kind=fixture) — not Option B proof."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.contracts.manifest import LabelWindow, ModelBundleManifest, TrainWindow
from alphaguard.ml.gate import write_manifest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fixtures" / "model_bundle_fixture"


def _synthetic_rows(n: int = 64) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    x = rng.normal(size=(n, len(FEATURE_NAMES)))
    # Higher vol + negative prior returns → higher risk label (synthetic only).
    logits = (
        1.5 * x[:, FEATURE_NAMES.index("volatility_20d")]
        - 1.2 * x[:, FEATURE_NAMES.index("return_5d_prior")]
        - 0.8 * x[:, FEATURE_NAMES.index("finbert_sentiment")]
    )
    y = (logits > 0).astype(int)
    return x, y


def main() -> None:
    x, y = _synthetic_rows()
    dtrain = xgb.DMatrix(x, label=y)
    params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "max_depth": 2,
        "eta": 0.3,
        "seed": 42,
    }
    booster = xgb.train(params, dtrain, num_boost_round=20)
    OUT.mkdir(parents=True, exist_ok=True)
    model_path = OUT / "model.json"
    booster.save_model(str(model_path))

    # Fit a simple threshold on synthetic train probs maximizing F1 (toy).
    probs = booster.predict(dtrain)
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.1, 0.9, 17):
        pred = (probs >= t).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)

    dataset_hash = hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest()[:16]
    manifest = ModelBundleManifest(
        bundle_id="fixture-downside-v1",
        model_version="0.1.0-fixture",
        bundle_kind="fixture",
        feature_names=list(FEATURE_NAMES),
        feature_dtypes={name: "float" for name in FEATURE_NAMES},
        score_kind="proba_high_risk",
        score_threshold=best_t,
        threshold_fitting="train_f1_max",
        vol_veto_enabled=False,
        vol_veto_threshold=None,
        policy_version="v1",
        label_definition="fwd_return_5d < -0.03",
        label_window=LabelWindow(
            start="first_completed_session_close_at_or_after_event_session",
            end="close_5_trading_sessions_later",
        ),
        train_window=TrainWindow(start="synthetic", end="synthetic"),
        dataset_hash=dataset_hash,
        dataset_source="scripts/build_fixture_bundle.py synthetic",
        metrics={"train_f1_at_threshold": best_f1, "n_rows": int(len(y))},
        library_versions={
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
        },
        created_at=datetime.now(timezone.utc),
        model_filename="model.json",
    )
    write_manifest(OUT / "manifest.json", manifest)
    meta = {"note": "bundle_kind=fixture — not Option B proof"}
    (OUT / "README.md").write_text(
        "# Fixture model bundle\n\n"
        "Synthetic XGBoost downside scorer for smoke plumbing only.\n"
        f"Threshold={best_t:.4f} (train F1 max on synthetic rows).\n"
        f"Meta: {json.dumps(meta)}\n",
        encoding="utf-8",
    )
    print(f"wrote fixture bundle to {OUT}")


if __name__ == "__main__":
    main()
