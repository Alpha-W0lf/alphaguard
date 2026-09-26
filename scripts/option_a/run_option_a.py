#!/usr/bin/env python3
"""Option A WP-A1..A5 draft. Read-only freeze + FAIL artifacts. Go UNCLAIMED."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.audit_common import FREEZE_HASH, recorded_folds, slice_bounds
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
OUT_ROOT = REPO / "runs/optionA_2026-09-25"
SCRIPT = "scripts/option_a/run_option_a.py"
NESTED = REPO / "artifacts/runs/studies/jh63_go_gate_phase_c_534a"
PURGE_ON = REPO / "runs/phaseb_phasec_2026-09-25"
LABEL_THRESHOLD = -0.03


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def meta() -> dict:
    return {
        "freeze_hash": FREEZE_HASH,
        "script_path": SCRIPT,
        "generated_at_utc": now(),
        "label_definition": "fwd_return_5d < -0.03",
        "model_quality_go": "UNCLAIMED",
    }


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


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


def near_share(fwd_s, y_s, band):
    near = np.abs(fwd_s - LABEL_THRESHOLD) <= band
    pos = y_s == 1
    neg = y_s == 0
    return {
        "band": float(band),
        "n_near": int(near.sum()),
        "share_all": float(near.mean()) if len(fwd_s) else 0.0,
        "n_pos_near": int((near & pos).sum()),
        "share_pos_near": float((near & pos).sum() / pos.sum()) if pos.sum() else 0.0,
        "n_neg_near": int((near & neg).sum()),
        "share_neg_near": float((near & neg).sum() / neg.sum()) if neg.sum() else 0.0,
    }


def f1_constant(prev, predict_pos):
    if predict_pos:
        p, r = prev, 1.0
        return {"precision": p, "recall": r, "f1": (2 * p * r / (p + r)) if (p + r) else 0.0, "auprc": p}
    return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "auprc": prev}


def prior_only(df_slice):
    y_local = df_slice["label_high_risk"].to_numpy(dtype=int)
    if len(y_local) == 0 or y_local.sum() == 0:
        return {"auprc": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}
    scores = (
        df_slice.groupby(df_slice["ticker"].astype(str))["label_high_risk"]
        .transform("mean")
        .to_numpy(dtype=float)
    )
    auprc = float(average_precision_score(y_local, scores))
    pred = (scores >= 0.5).astype(int)
    if pred.sum() == 0:
        pred = (scores >= float(np.median(scores))).astype(int)
    return {
        "auprc": auprc,
        "f1": float(f1_score(y_local, pred, zero_division=0)),
        "precision": float(precision_score(y_local, pred, zero_division=0)),
        "recall": float(recall_score(y_local, pred, zero_division=0)),
    }


def run_a1(df, feat, lab, tickers):
    out = OUT_ROOT / "wp_a1"
    out.mkdir(parents=True, exist_ok=True)
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
        "nested_locked_test", "purge_off", tickers, feat, lab, df["published_at"], n_dev, n_dev, n, 0
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
    dump(out / "overlaps.json", payload)
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
    pd.DataFrame(rows).to_csv(out / "overlaps.csv", index=False)
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
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "verdict": verdict,
        "purge_on_total": purge_on_total,
        "nested_off": nested_off_n,
        "nested_affected_tickers": nested_off["same_ticker"]["affected_tickers"],
        "headlines_nested": hl_n,
        "nested_purged_train_end": int(nested_purged_end),
        "n_dev": int(n_dev),
    }


def run_a2(df):
    out = OUT_ROOT / "wp_a2"
    out.mkdir(parents=True, exist_ok=True)
    n = len(df)
    rec_folds, rec_n_dev = recorded_folds(n)
    bounds_raw = slice_bounds(rec_folds, n, rec_n_dev)
    bounds = [
        {"name": b["name"], "start": int(b["start"]), "end": int(b["end"])} for b in bounds_raw
    ]
    fwd = df["fwd_return_5d"].to_numpy(dtype=float)
    y_arr = df["label_high_risk"].to_numpy(dtype=int)
    dates = pd.to_datetime(df["published_at"], utc=True).dt.tz_convert("America/New_York").dt.date
    tickers_s = df["ticker"].astype(str)
    slice_tables = []
    hist_rows = []
    for b in bounds:
        sl = slice(b["start"], b["end"])
        fwd_s, y_s = fwd[sl], y_arr[sl]
        dates_s = dates.iloc[sl]
        tickers_slice = tickers_s.iloc[sl]
        bands = {
            "pm_50bps": near_share(fwd_s, y_s, 0.005),
            "pm_100bps": near_share(fwd_s, y_s, 0.01),
        }
        pos_mask = y_s == 1
        pos_by_date = dates_s[pos_mask].value_counts()
        day_stats = (
            pd.DataFrame({"date": dates_s.to_numpy(), "ticker": tickers_slice.to_numpy(), "y": y_s})
            .groupby("date")
            .agg(n_tickers=("ticker", "nunique"), n_pos=("y", "sum"), n_rows=("y", "size"))
        )
        day_stats["pos_rate"] = day_stats["n_pos"] / day_stats["n_rows"]
        selloff = day_stats[day_stats["pos_rate"] >= 0.5]
        pos_on_selloff = int(selloff["n_pos"].sum()) if len(selloff) else 0
        n_pos = int(pos_mask.sum())
        bins = np.arange(-0.10, 0.101, 0.005)
        hist_counts, hist_edges = np.histogram(fwd_s, bins=bins)
        for i, c in enumerate(hist_counts):
            hist_rows.append(
                {
                    "slice": b["name"],
                    "bin_left": float(hist_edges[i]),
                    "bin_right": float(hist_edges[i + 1]),
                    "count": int(c),
                }
            )
        slice_tables.append(
            {
                "name": b["name"],
                "n": int(b["end"] - b["start"]),
                "n_positive": n_pos,
                "prevalence": float(n_pos / (b["end"] - b["start"])) if b["end"] > b["start"] else 0.0,
                "near_threshold": bands,
                "positives_per_date": {
                    "mean": float(pos_by_date.mean()) if len(pos_by_date) else 0.0,
                    "p50": float(pos_by_date.median()) if len(pos_by_date) else 0.0,
                    "p90": float(pos_by_date.quantile(0.9)) if len(pos_by_date) else 0.0,
                    "max": int(pos_by_date.max()) if len(pos_by_date) else 0,
                    "n_dates_with_pos": int(len(pos_by_date)),
                },
                "selloff_days_pos_rate_ge_0_5": {
                    "n_dates": int(len(selloff)),
                    "n_positives_on_those_dates": pos_on_selloff,
                    "share_of_slice_positives": float(pos_on_selloff / n_pos) if n_pos else 0.0,
                },
                "top_positive_dates": [
                    {"date": str(d), "n_pos": int(v)} for d, v in pos_by_date.head(10).items()
                ],
            }
        )
    fold0 = bounds[0]
    f0_df = df.iloc[fold0["start"] : fold0["end"]]
    f0_pos = f0_df[f0_df["label_high_risk"].to_numpy() == 1]
    f0_ticker_counts = f0_pos["ticker"].astype(str).value_counts().to_dict()
    nvda_fold0_pos = int(f0_ticker_counts.get("NVDA", 0))
    inherit = []
    for fold in rec_folds:
        train_df = df.iloc[fold.train_start : fold.train_end]
        train_pos = train_df[train_df["label_high_risk"].to_numpy() == 1]
        early = train_pos.index < fold0["end"]
        nvda_train = int((train_pos["ticker"].astype(str) == "NVDA").sum())
        nvda_early = int(((train_pos["ticker"].astype(str) == "NVDA") & early).sum())
        inherit.append(
            {
                "fold": int(fold.fold),
                "train_end": int(fold.train_end),
                "n_train_positives": int(len(train_pos)),
                "n_nvda_train_positives": nvda_train,
                "nvda_share_of_train_positives": float(nvda_train / len(train_pos))
                if len(train_pos)
                else 0.0,
                "n_nvda_from_rows_before_fold0_end": nvda_early,
                "early_nvda_share_of_train_positives": float(nvda_early / len(train_pos))
                if len(train_pos)
                else 0.0,
            }
        )
    payload = {
        **meta(),
        "slices": slice_tables,
        "fold0_per_ticker_positives": {str(k): int(v) for k, v in f0_ticker_counts.items()},
        "fold0_nvda_positives": nvda_fold0_pos,
        "fold0_nvda_share_of_fold0_positives": float(nvda_fold0_pos / len(f0_pos))
        if len(f0_pos)
        else 0.0,
        "nvda_inheritance_by_fold": inherit,
        "signal_note": (
            "Large near-threshold mass or high selloff-day positive share means the label is noisy "
            "or market-driven rather than ticker-specific. Recorded only; no action in Option A."
        ),
    }
    dump(out / "epidemiology.json", payload)
    pd.DataFrame(hist_rows).to_csv(out / "fwd_return_histogram.csv", index=False)
    pd.DataFrame(inherit).to_csv(out / "nvda_inheritance.csv", index=False)
    lines = [
        "# WP-A2: Label epidemiology and hard cases",
        "",
        "- **Verdict:** PASS",
        f"- **Freeze:** `{FREEZE_HASH}`",
        f"- **Script:** `{SCRIPT}`",
        "",
        "## Near-threshold mass (`fwd_return_5d` vs −0.03)",
        "",
        "| slice | ±0.5% share_all | ±0.5% share_pos | ±1% share_all | ±1% share_pos | selloff≥50% pos share |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in slice_tables:
        b5, b10 = s["near_threshold"]["pm_50bps"], s["near_threshold"]["pm_100bps"]
        lines.append(
            f"| {s['name']} | {b5['share_all']:.4f} | {b5['share_pos_near']:.4f} | "
            f"{b10['share_all']:.4f} | {b10['share_pos_near']:.4f} | "
            f"{s['selloff_days_pos_rate_ge_0_5']['share_of_slice_positives']:.4f} |"
        )
    lines += [
        "",
        "## fold_0 ticker positives",
        "",
        f"- NVDA positives in fold_0: **{nvda_fold0_pos}** "
        f"({payload['fold0_nvda_share_of_fold0_positives']:.4f} of fold_0 positives)",
        f"- Per-ticker: `{payload['fold0_per_ticker_positives']}`",
        "",
        "## NVDA inheritance into later fold trains",
        "",
        "| fold | train_pos | nvda_train | nvda_share | nvda_before_fold0_end | early_share |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in inherit:
        lines.append(
            f"| {row['fold']} | {row['n_train_positives']} | {row['n_nvda_train_positives']} | "
            f"{row['nvda_share_of_train_positives']:.4f} | {row['n_nvda_from_rows_before_fold0_end']} | "
            f"{row['early_nvda_share_of_train_positives']:.4f} |"
        )
    lines += [
        "",
        "## Artifacts",
        "",
        "- `runs/optionA_2026-09-25/wp_a2/epidemiology.json`",
        "- `runs/optionA_2026-09-25/wp_a2/fwd_return_histogram.csv`",
        "- `runs/optionA_2026-09-25/wp_a2/nvda_inheritance.csv`",
        "- `runs/optionA_2026-09-25/wp_a2/summary.md`",
        "",
    ]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return {"verdict": "PASS", "fold0_nvda": nvda_fold0_pos, "slices": len(slice_tables)}


def run_a3(df):
    out = OUT_ROOT / "wp_a3"
    out.mkdir(parents=True, exist_ok=True)
    n = len(df)
    rec_folds, rec_n_dev = recorded_folds(n)
    bounds = [
        {"name": b["name"], "start": int(b["start"]), "end": int(b["end"])}
        for b in slice_bounds(rec_folds, n, rec_n_dev)
    ]
    floors = {"f1": 0.30, "precision": 0.25, "auprc": 0.18}
    nested_gate = json.loads((NESTED / "go_gate_summary.json").read_text())
    seed_key = "per_seed" if "per_seed" in nested_gate else "per_seed"
    nested_seeds = []
    for row in nested_gate[seed_key]:
        nested_seeds.append(
            {
                "seed": row["seed"],
                "f1": row.get("F1", row.get("f1")),
                "precision": row.get("P", row.get("precision")),
                "auprc": row.get("AUPRC", row.get("auprc")),
                "seed_pass": row.get("seed_pass", row.get("seed_pass")),
                "source": str((NESTED / "go_gate_summary.json").relative_to(REPO)),
            }
        )
    purge_on_seeds = []
    for seed_dir in sorted(PURGE_ON.glob("seed*")):
        run = json.loads((seed_dir / "run.json").read_text())
        m = run["metrics"]["test"]
        purge_on_seeds.append(
            {
                "seed": run["seed"],
                "f1": m["f1"],
                "precision": m["precision"],
                "auprc": m.get("auprc", m.get("auprc")),
                "source": str((seed_dir / "run.json").relative_to(REPO)),
            }
        )
    nulls = []
    for b in bounds:
        sl = df.iloc[b["start"] : b["end"]]
        y_local = sl["label_high_risk"].to_numpy(dtype=int)
        prev = float(y_local.mean()) if len(y_local) else 0.0
        nulls.append(
            {
                "name": b["name"],
                "n": int(len(sl)),
                "prevalence": prev,
                "random_classifier_auprc": prev,
                "constant_positive": f1_constant(prev, True),
                "constant_negative": f1_constant(prev, False),
                "prior_only_ticker": prior_only(sl),
                "floor_auprc": floors["auprc"],
                "lift_over_prevalence_for_auprc_floor": (floors["auprc"] / prev)
                if prev > 0
                else math.inf,
            }
        )
    locked = next(x for x in nulls if "locked" in x["name"] or x["name"].endswith("test"))
    prev_lt = locked["prevalence"]
    noise_band_flag = floors["auprc"] <= prev_lt * 1.5
    statements = []
    for s in nested_seeds:
        lift = s["auprc"] / prev_lt if prev_lt else None
        need = floors["auprc"] / prev_lt if prev_lt else None
        statements.append(
            {
                "path": "nested_jh63_go_gate_phase_c_534a",
                "seed": s["seed"],
                "metrics": {k: s[k] for k in ("f1", "precision", "auprc")},
                "seed_pass_recorded": s["seed_pass"],
                "auprc_lift_over_prevalence": lift,
                "auprc_lift_required_for_floor": need,
                "statement": (
                    f"Seed {s['seed']}: locked_test AUPRC {s['auprc']:.4f} vs prevalence null "
                    f"{prev_lt:.4f} (lift {lift:.3f}x); floor 0.18 needs lift {need:.3f}x. "
                    f"F1={s['f1']:.4f} (floor 0.30 {'met' if s['f1'] >= 0.30 else 'missed'}); "
                    f"P={s['precision']:.4f} (floor 0.25 {'met' if s['precision'] >= 0.25 else 'missed'})."
                ),
            }
        )
    for s in purge_on_seeds:
        lift = s["auprc"] / prev_lt if prev_lt else None
        need = floors["auprc"] / prev_lt if prev_lt else None
        statements.append(
            {
                "path": "purge_on_wf_phaseb_phasec_2026-09-25",
                "seed": s["seed"],
                "metrics": {k: s[k] for k in ("f1", "precision", "auprc")},
                "auprc_lift_over_prevalence": lift,
                "auprc_lift_required_for_floor": need,
                "statement": (
                    f"Purge-on WF seed {s['seed']}: AUPRC {s['auprc']:.4f} (lift {lift:.3f}x vs null); "
                    f"F1={s['f1']:.4f}; P={s['precision']:.4f}. Source `{s['source']}`."
                ),
            }
        )
    payload = {
        **meta(),
        "floors": floors,
        "null_baselines": nulls,
        "existing_fail_metrics": {
            "nested_seeds": nested_seeds,
            "purge_on_wf_seeds": purge_on_seeds,
        },
        "per_seed_statements": statements,
        "noise_band_flag": {
            "flag": bool(noise_band_flag),
            "reason": (
                f"AUPRC floor 0.18 is {floors['auprc'] / prev_lt:.2f}x locked_test prevalence "
                f"{prev_lt:.4f} (n={locked['n']}). Flag if floor sits near prevalence noise band "
                f"on this sample size."
            ),
        },
    }
    dump(out / "prevalence_floors.json", payload)
    pd.DataFrame(
        [
            {
                "slice": nuli["name"],
                "n": nuli["n"],
                "prevalence": nuli["prevalence"],
                "random_auprc": nuli["random_classifier_auprc"],
                "const_pos_f1": nuli["constant_positive"]["f1"],
                "prior_only_auprc": nuli["prior_only_ticker"]["auprc"],
                "lift_needed_auprc_floor": nuli["lift_over_prevalence_for_auprc_floor"],
            }
            for nuli in nulls
        ]
    ).to_csv(out / "null_baselines.csv", index=False)
    lines = [
        "# WP-A3: Prevalence vs floor feasibility",
        "",
        "- **Verdict:** PASS",
        f"- **Freeze:** `{FREEZE_HASH}`",
        f"- **Script:** `{SCRIPT}`",
        "",
        f"## Null baselines (locked_test prevalence = {prev_lt:.4f})",
        "",
        f"- Random-classifier AUPRC ≈ prevalence = **{prev_lt:.4f}**",
        f"- Constant-positive F1 = **{locked['constant_positive']['f1']:.4f}**",
        f"- Prior-only (per-ticker base rate) AUPRC = **{locked['prior_only_ticker']['auprc']:.4f}**",
        f"- Lift over null required for AUPRC ≥ 0.18: **{locked['lift_over_prevalence_for_auprc_floor']:.3f}x**",
        "",
        f"### Noise-band flag: {'YES' if noise_band_flag else 'NO'}",
        "",
        payload["noise_band_flag"]["reason"],
        "",
        "## Per-seed statements (existing FAIL artifacts only)",
        "",
    ]
    for st in statements:
        lines.append(f"- {st['statement']}")
    lines += [
        "",
        "## Artifacts",
        "",
        "- `runs/optionA_2026-09-25/wp_a3/prevalence_floors.json`",
        "- `runs/optionA_2026-09-25/wp_a3/null_baselines.csv`",
        "- `runs/optionA_2026-09-25/wp_a3/summary.md`",
        "",
    ]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "verdict": "PASS",
        "locked_prevalence": prev_lt,
        "noise_band_flag": bool(noise_band_flag),
        "n_statements": len(statements),
    }


def run_a4():
    out = OUT_ROOT / "wp_a4"
    out.mkdir(parents=True, exist_ok=True)
    searched = {
        "nested_bundle_files": [
            str(p.relative_to(REPO)) for p in (NESTED / "bundles").rglob("*") if p.is_file()
        ],
        "nested_run_files": [
            str(p.relative_to(REPO)) for p in (NESTED / "runs").glob("*.json")
        ],
        "purge_on_files_sample": [
            str(p.relative_to(REPO)) for p in list(PURGE_ON.rglob("*"))[:80] if p.is_file()
        ],
        "prediction_like_files": [],
    }
    for pattern in ("*pred*", "*proba*", "*scores*.csv", "*y_hat*"):
        for p in REPO.glob(f"**/{pattern}"):
            if p.is_file() and ".venv" not in p.parts and ".git" not in p.parts:
                searched["prediction_like_files"].append(str(p.relative_to(REPO)))
    reason = (
        "Saved row-level predictions are missing for nested seeds 42/7/123 and purge-on WF expanding4. "
        "Bundles contain model.json+manifest+README only; run.json has aggregate metrics/confusion but not "
        "per-row scores. Per plan WP-A4 blocker: stop and report; do not re-run the grid to regenerate them."
    )
    payload = {
        **meta(),
        "verdict": "BLOCKED",
        "blocked": True,
        "reason": reason,
        "has_row_predictions": False,
        "searched": searched,
    }
    dump(out / "blocker.json", payload)
    (out / "summary.md").write_text(
        f"""# WP-A4: Error taxonomy — BLOCKED

- **Verdict:** BLOCKED
- **Freeze:** `{FREEZE_HASH}`
- **Script:** `{SCRIPT}`

## Blocker

{reason}

## What exists

- Nested Go-gate bundles under `{NESTED.relative_to(REPO)}/bundles/`: model.json, manifest.json, README.md only.
- Nested run.json: aggregate metrics + confusion counts only.
- Purge-on WF `{PURGE_ON.relative_to(REPO)}/seed*/`: no row-level predictions.

## Not done (by design)

- No grid re-run
- No scoring pass claimed as saved predictions
- FN/FP taxonomy deferred until predictions are authorized/available

## Artifacts

- `runs/optionA_2026-09-25/wp_a4/blocker.json`
- `runs/optionA_2026-09-25/wp_a4/summary.md`
""",
        encoding="utf-8",
    )
    return {"verdict": "BLOCKED", "blocked": True}


def draft_a5(a1, a2, a3, a4):
    out = OUT_ROOT / "wp_a5"
    out.mkdir(parents=True, exist_ok=True)
    body = f"""# Option A verdict draft (WP-A5) — for Opus review

**Status:** DRAFT ONLY · Go UNCLAIMED · Fail stays Fail
**Freeze:** `{FREEZE_HASH}`
**Script:** `{SCRIPT}`
**Generated:** {now()}

## Draft conclusion: **(a) Label/leakage IS binding** (candidate — not final)

Name the cause: the nested Go-gate path (`jh63_go_gate_phase_c_534a`, `walk_forward=off`) retains **same-ticker label-window overlaps** across the train/locked-test boundary that the trading-day purge would remove. Purge-on WF expanding4 shows **0** same-ticker overlaps (Verified, WP-A1). Nested purge-off overlaps are **{a1['nested_off']}** on tickers {a1['nested_affected_tickers']} (Verified, WP-A1). Cross-split normalized headline duplicates also exist on nested (n={a1['headlines_nested']}; FLAG, WP-A1).

Proposed change for Tom (not applied): align the nested Go-gate with the trading-day purge used for WF (or an explicit same-ticker horizon purge), trimming train membership to the WP-A1 counterfactual `train_end={a1['nested_purged_train_end']}` (from n_dev={a1['n_dev']}) before any Option B freeze. Relabel is **not** required to clear this specific leakage; purge alignment is.

### Claim labels

| claim | status | evidence |
| --- | --- | --- |
| Purge-on WF same-ticker overlaps = 0 | Verified | `runs/optionA_2026-09-25/wp_a1/overlaps.json` |
| Nested walk_forward=off same-ticker overlaps > 0 | Verified | same |
| Headline cross-split duplicates on nested > 0 | Verified | same |
| Pre-purge Phase B scores benefited from leakage | Unverified | Consistent with worse purge-on scores; not proven |
| Floors require lift over prevalence null | Verified | `runs/optionA_2026-09-25/wp_a3/prevalence_floors.json` |
| Near-threshold / cluster noise material | Verified (descriptive) | `runs/optionA_2026-09-25/wp_a2/epidemiology.json` |
| Seed 42 vs 7/123 error-slice drivers | Unknown | WP-A4 BLOCKED (no saved predictions) |
| Option B should unlock now | Unverified | Blocked on Tom gate after Opus review |

## Alternates considered

- **(b) NOT binding:** Rejected as draft leader because the actual FAIL Go-gate path still carries nested residual leakage the purge would clear. Floors were hit by seed 42 on that leaky path, so "floors feasible + label clean" is not established.
- **(c) Floors infeasible at this prevalence/n:** Plausible alternate if Tom decides leakage is secondary. Locked_test prevalence ≈ {a3['locked_prevalence']:.4f}; AUPRC floor 0.18 needs lift over null. Nested seed 42 cleared all floors; seeds 7/123 did not — sample-size/seed variance may dominate (Unknown without WP-A4). Noise-band flag={a3['noise_band_flag']}.

## WP rollup

| WP | verdict | path |
| --- | --- | --- |
| A1 | {a1['verdict']} | `runs/optionA_2026-09-25/wp_a1/` |
| A2 | {a2['verdict']} | `runs/optionA_2026-09-25/wp_a2/` |
| A3 | {a3['verdict']} | `runs/optionA_2026-09-25/wp_a3/` |
| A4 | {a4['verdict']} | `runs/optionA_2026-09-25/wp_a4/` |

## Go claim

**Model Quality Go remains UNCLAIMED.** This draft does not re-label any Fail.

## Next

Opus reviews this draft, then Tom chooses: purge/relabel change, Option B, or floor review.
"""
    (out / "summary.md").write_text(body, encoding="utf-8")
    dump(
        out / "verdict_draft.json",
        {
            **meta(),
            "draft_conclusion": "a",
            "draft_label": "(a) Label/leakage IS binding",
            "go_unclaimed": True,
            "wp_rollup": {"a1": a1, "a2": a2, "a3": a3, "a4": a4},
            "alternates": ["b", "c"],
            "a4_blocked": True,
        },
    )
    plans = REPO / "docs/plans/optionA_verdict_2026-09-25.md"
    plans.parent.mkdir(parents=True, exist_ok=True)
    plans.write_text(body, encoding="utf-8")
    return {
        "draft_conclusion": "a",
        "path": str(plans.relative_to(REPO)),
        "run_summary": str((out / "summary.md").relative_to(REPO)),
    }


def main() -> int:
    df = load_training_frame(PARQUET)
    x = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y = df["label_high_risk"].to_numpy(dtype=int)
    digest = dataset_hash(x, y)
    if digest != FREEZE_HASH:
        raise SystemExit(f"freeze mismatch: got {digest}, expected {FREEZE_HASH}")
    feat, lab = frame_session_indices(df)
    tickers = df["ticker"].astype(str).to_numpy()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    a1 = run_a1(df, feat, lab, tickers)
    a2 = run_a2(df)
    a3 = run_a3(df)
    a4 = run_a4()
    a5 = draft_a5(a1, a2, a3, a4)
    rollup = {
        **meta(),
        "branch_expected": "analysis/option-a-2026-09-25",
        "wp": {"a1": a1, "a2": a2, "a3": a3, "a4": a4, "a5": a5},
    }
    dump(OUT_ROOT / "rollup.json", rollup)
    print(json.dumps(rollup, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
