#!/usr/bin/env python3
"""One-shot: nested walk_forward=off uses locked-test trading-day purge (train_end 7029)."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.audit_common import FREEZE_HASH
from alphaguard.ml.dataset_asof import frame_session_indices
from alphaguard.ml.study_walkforward import prefix_end_before_session, split_for_walk_forward
from alphaguard.ml.train_option_b import dataset_hash, load_training_frame

REPO = Path(__file__).resolve().parents[2]
PARQUET = REPO / "data/derived/training_events.parquet"
OUT_DIR = REPO / "runs/optionA_2026-09-25/purge_align"
OUT_JSON = OUT_DIR / "check.json"
SCRIPT = "scripts/option_a/nested_purge_align_check.py"
OVERLAPS = REPO / "runs/optionA_2026-09-25/wp_a1/overlaps.json"
ROLLUP = REPO / "runs/optionA_2026-09-25/rollup.json"

BOUNDARY = 7125
EXPECTED_TRAIN = 7029


def _load_same_ticker_overlaps():
    path = REPO / "scripts/option_a/wp_a1_residual_leakage.py"
    spec = importlib.util.spec_from_file_location("wp_a1_residual_leakage", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.same_ticker_overlaps


def main() -> int:
    same_ticker_overlaps = _load_same_ticker_overlaps()
    df = load_training_frame(PARQUET)
    x = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y = df["label_high_risk"].to_numpy(dtype=int)
    digest = dataset_hash(x, y)
    if digest != FREEZE_HASH:
        raise SystemExit(f"freeze mismatch: {digest} != {FREEZE_HASH}")

    n = len(df)
    split = split_for_walk_forward(df, 0.8, "off")
    n_train = int(len(split.y_train))
    n_test = int(len(split.y_test))
    if n_train != EXPECTED_TRAIN:
        raise SystemExit(f"n_train={n_train} expected {EXPECTED_TRAIN}")
    if n_test != n - BOUNDARY:
        raise SystemExit(f"n_test={n_test} expected {n - BOUNDARY} (test start {BOUNDARY})")

    feat, lab = frame_session_indices(df)
    tickers = df["ticker"].astype(str).to_numpy()
    published_at = df["published_at"]
    overlaps = same_ticker_overlaps(
        tickers,
        feat,
        lab,
        published_at,
        train_end=EXPECTED_TRAIN,
        test_start=BOUNDARY,
        test_end=n,
    )
    overlap_rows = int(overlaps["overlap_train_rows"])
    if overlap_rows != 0:
        raise SystemExit(f"same-ticker overlaps={overlap_rows} expected 0")

    next_session = int(np.min(feat[BOUNDARY:]))
    purged_end = int(
        prefix_end_before_session(lab, candidate_end=BOUNDARY, next_session=next_session)
    )
    if purged_end != EXPECTED_TRAIN:
        raise SystemExit(f"prefix_end_before_session={purged_end} expected {EXPECTED_TRAIN}")

    ov = json.loads(OVERLAPS.read_text())
    cf_end = int(ov["nested_path"]["purge_on_counterfactual"]["train_end"])
    if cf_end != EXPECTED_TRAIN:
        raise SystemExit(f"overlaps.json counterfactual train_end={cf_end} != {EXPECTED_TRAIN}")
    roll = json.loads(ROLLUP.read_text())
    roll_end = roll.get("wp", {}).get("a1", {}).get("nested_purged_train_end")
    if roll_end is None:
        # try alternate paths
        for key in ("wp.a1.nested_purged_train_end",):
            pass
        # flatten search
        def find(obj, target="nested_purged_train_end"):
            if isinstance(obj, dict):
                if target in obj:
                    return obj[target]
                for v in obj.values():
                    r = find(v, target)
                    if r is not None:
                        return r
            return None

        roll_end = find(roll)
    if int(roll_end) != EXPECTED_TRAIN:
        raise SystemExit(f"rollup nested_purged_train_end={roll_end} != {EXPECTED_TRAIN}")

    payload = {
        "freeze_hash": FREEZE_HASH,
        "dataset_hash": digest,
        "dataset_hash_match": True,
        "script_path": SCRIPT,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "walk_forward": "off",
        "n_rows": n,
        "boundary_test_start": BOUNDARY,
        "n_train": n_train,
        "n_test": n_test,
        "prefix_end_before_session": purged_end,
        "same_ticker_overlap_train_rows": overlap_rows,
        "wp_a1_purge_on_counterfactual_train_end": cf_end,
        "rollup_nested_purged_train_end": int(roll_end),
        "model_quality_go": "UNCLAIMED",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
