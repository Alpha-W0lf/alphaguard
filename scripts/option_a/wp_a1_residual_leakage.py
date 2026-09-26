#!/usr/bin/env python3
"""WP-A1: residual same-ticker label-window leakage beyond C3 (read-only)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.audit_common import FREEZE_HASH
from alphaguard.ml.dataset_asof import frame_session_indices
from alphaguard.ml.dataset_ingest import normalize_headline
from alphaguard.ml.study_walkforward import (
    apply_trading_day_embargo,
    expanding4_folds,
    horizon_overlap_count,
    prefix_end_before_session,
)
from alphaguard.ml.train_option_b import dataset_hash, load_training_frame

REPO = Path(__file__).resolve().parents[2]
PARQUET = REPO / "data/derived/training_events.parquet"
OUT = REPO / "runs/optionA_2026-09-25/wp_a1"
SCRIPT = "scripts/option_a/wp_a1_residual_leakage.py"


def meta():
    return {
        "freeze_hash": FREEZE_HASH,
        "script_path": SCRIPT,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "label_definition": "fwd_return_5d < -0.03",
        "model_quality_go": "UNCLAIMED",
    }


def same_ticker_overlaps(tickers, feat, lab, published_at, train_end, test_start, test_end, max_details=40):
    details = []
    by_ticker = {}
    overlap_rows = 0
    for tkr in sorted(set(tickers[test_start:test_end].tolist())):
        tr_idx = np.flatnonzero(tickers[:train_end] == tkr)
        te_idx = np.flatnonzero(tickers[test_start:test_end] == tkr) + test_start
        if len(tr_idx) == 0 or len(te_idx) == 0:
            continue
        te_feat_sorted = np.sort(feat[te_idx])
        n_t = 0
        for i in tr_idx:
            lo = int(feat[i])
            hi = int(lab[i])
            left = int(np.searchsorted(te_feat_sorted, lo, side="right"))
            right = int(np.searchsorted(te_feat_sorted, hi, side="right"))
            if right > left:
                n_t += 1
                if len(details) < max_details:
                    details.append(
                        {
                            "train_row": int(i),
                            "ticker": str(tkr),
                            "feature_session": lo,
                            "label_end_session": hi,
                            "n_overlapping_test_rows": int(right - left),
                            "published_at": str(published_at.iloc[i]),
                        }
                    )
        if n_t:
            by_ticker[str(tkr)] = int(n_t)
            overlap_rows += n_t
    return {
        "overlap_train_rows": int(overlap_rows),
        "affected_tickers": sorted(by_ticker),
        "by_ticker": by_ticker,
        "details_sample": details,
    }


def headline_cross(headlines, tickers, published_at, left_end, right_start, right_end):
    norms = headlines.map(normalize_headline)
    hashes = norms.map(lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())
    left = hashes.iloc[:left_end]
    right = hashes.iloc[right_start:right_end]
    shared = set(left) & set(right)
    samples = []
    for h in list(shared)[:25]:
        l_rows = left.index[left == h].tolist()[:3]
        r_rows = right.index[right == h].tolist()[:3]
        samples.append(
            {
                "headline_sha256": h,
                "normalized": norms.iloc[l_rows[0]] if l_rows else None,
                "left_rows": [int(i) for i in l_rows],
                "right_rows": [int(i) for i in r_rows],
                "left_tickers": [str(tickers[i]) for i in l_rows],
                "right_tickers": [str(tickers[i]) for i in r_rows],
            }
        )
    return {
        "shared_normalized_headline_hashes": int(len(shared)),
        "left_unique": int(left.nunique()),
        "right_unique": int(right.nunique()),
        "samples": samples,
    }


def pack(name, mode, tickers, feat, lab, published_at, train_end, test_start, test_end, embargo_rows):
    return {
        "name": name,
        "mode": mode,
        "train_end": int(train_end),
        "test_start": int(test_start),
        "test_end": int(test_end),
        "embargo_rows": int(embargo_rows),
        "global_session_overlap_rows": int(
            horizon_overlap_count(lab, feat, train_end, test_start, test_end)
        ),
        "same_ticker": same_ticker_overlaps(
            tickers, feat, lab, published_at, train_end, test_start, test_end
        ),
    }


def main() -> int:
    df = load_training_frame(PARQUET)
    x = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y = df["label_high_risk"].to_numpy(dtype=int)
    digest = dataset_hash(x, y)
    if digest != FREEZE_HASH:
        raise SystemExit(f"freeze mismatch: {digest} != {FREEZE_HASH}")

    feat, lab = frame_session_indices(df)
    tickers = df["ticker"].astype(str).to_numpy()
    n = len(df)
    folds, n_dev, src = expanding4_folds(n, embargo_rows=5)
    purged, changed = apply_trading_day_embargo(folds, lab, feat)

    wf_off = [
        pack(
            f"fold_{f.fold}",
            "purge_off",
            tickers,
            feat,
            lab,
            df["published_at"],
            f.train_end,
            f.val_start,
            f.val_end,
            f.embargo_rows,
        )
        for f in folds
    ]
    wf_on = [
        pack(
            f"fold_{f.fold}",
            "purge_on",
            tickers,
            feat,
            lab,
            df["published_at"],
            f.train_end,
            f.val_start,
            f.val_end,
            f.embargo_rows,
        )
        for f in purged
    ]

    nested_off = pack(
        "nested_locked_test",
        "purge_off",
        tickers,
        feat,
        lab,
        df["published_at"],
        n_dev,
        n_dev,
        n,
        0,
    )
    nested_purged_end = prefix_end_before_session(
        lab, candidate_end=n_dev, next_session=int(np.min(feat[n_dev:n]))
    )
    nested_on = pack(
        "nested_locked_test",
        "purge_on_counterfactual",
        tickers,
        feat,
        lab,
        df["published_at"],
        nested_purged_end,
        n_dev,
        n,
        n_dev - nested_purged_end,
    )

    headlines_nested = headline_cross(df["headline"], tickers, df["published_at"], n_dev, n_dev, n)
    headlines_wf = [
        {
            "name": f"fold_{f.fold}",
            **headline_cross(
                df["headline"], tickers, df["published_at"], f.train_end, f.val_start, f.val_end
            ),
        }
        for f in folds
    ]

    purge_on_total = int(sum(r["same_ticker"]["overlap_train_rows"] for r in wf_on))
    purge_off_total = int(sum(r["same_ticker"]["overlap_train_rows"] for r in wf_off))
    nested_off_n = int(nested_off["same_ticker"]["overlap_train_rows"])
    hl_n = int(headlines_nested["shared_normalized_headline_hashes"])

    payload = {
        **meta(),
        "embargo_source_recorded": src,
        "n_rows": n,
        "n_dev": int(n_dev),
        "purge_changed_folds": bool(changed),
        "walk_forward_expanding4": {
            "purge_off": wf_off,
            "purge_on": wf_on,
            "purge_on_same_ticker_total": purge_on_total,
            "purge_off_same_ticker_total": purge_off_total,
        },
        "nested_path": {
            "study_id": "jh63_go_gate_phase_c_534a",
            "walk_forward": "off",
            "purge_off": nested_off,
            "purge_on_counterfactual": nested_on,
        },
        "headline_duplicates": {"nested": headlines_nested, "walk_forward_purge_off": headlines_wf},
        "pass_criteria": {
            "purge_on_wf_same_ticker_overlaps_zero": purge_on_total == 0,
            "nested_overlap_quantified": True,
        },
        "question_pre_purge_phase_b_leakage": (
            "Purge-off WF and nested paths show non-zero same-ticker label-window overlaps; "
            "purge-on WF is zero. Worse purge-on Phase B scores are consistent with a pre-purge "
            "leakage benefit, but do not prove it (overlap counts Verified; causal claim Unverified)."
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "overlaps.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    rows = []
    for block in (wf_off, wf_on, [nested_off, nested_on]):
        for r in block:
            rows.append(
                {
                    "split": r["name"],
                    "mode": r["mode"],
                    "train_end": r["train_end"],
                    "test_start": r["test_start"],
                    "test_end": r["test_end"],
                    "global_session_overlap_rows": r["global_session_overlap_rows"],
                    "same_ticker_overlap_rows": r["same_ticker"]["overlap_train_rows"],
                    "affected_tickers": "|".join(r["same_ticker"]["affected_tickers"]),
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "overlaps.csv", index=False)

    verdict = "PASS" if purge_on_total == 0 else "FAIL"
    if hl_n > 0 and purge_on_total == 0:
        verdict = "PASS_WITH_FLAG"

    lines = [
        "# WP-A1: Residual leakage beyond C3",
        "",
        f"- **Verdict:** {verdict}",
        f"- **Freeze:** `{FREEZE_HASH}`",
        f"- **Script:** `{SCRIPT}`",
        "- **Label:** `fwd_return_5d < -0.03` (unchanged)",
        "",
        "## Same-ticker label-window overlaps",
        "",
        "| split | purge_off | purge_on |",
        "| --- | ---: | ---: |",
    ]
    for off, on in zip(wf_off, wf_on):
        lines.append(
            f"| {off['name']} | {off['same_ticker']['overlap_train_rows']} | "
            f"{on['same_ticker']['overlap_train_rows']} |"
        )
    lines += [
        f"| nested_locked_test | {nested_off_n} | "
        f"{nested_on['same_ticker']['overlap_train_rows']} (counterfactual) |",
        "",
        f"- Purge-on WF total same-ticker overlaps: **{purge_on_total}** (pass requires 0).",
        f"- Nested Go-gate (`walk_forward=off`) same-ticker overlaps: **{nested_off_n}** "
        f"tickers={nested_off['same_ticker']['affected_tickers']}.",
        f"- Nested counterfactual trading-day purge: train_end {n_dev}→{nested_purged_end}; "
        f"overlaps → {nested_on['same_ticker']['overlap_train_rows']}.",
        "",
        "## Headline cross-split duplicates (normalized sha256)",
        "",
        f"- Nested shared hashes: **{hl_n}** (flag if > 0; listed in overlaps.json).",
        "",
        "## Question: did pre-purge Phase B benefit from leakage?",
        "",
        payload["question_pre_purge_phase_b_leakage"],
        "",
        "## Artifacts",
        "",
        "- `runs/optionA_2026-09-25/wp_a1/overlaps.json`",
        "- `runs/optionA_2026-09-25/wp_a1/overlaps.csv`",
        "- `runs/optionA_2026-09-25/wp_a1/summary.md`",
        "",
    ]
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "purge_on_total": purge_on_total, "nested_off": nested_off_n, "headlines": hl_n}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
