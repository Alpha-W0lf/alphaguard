#!/usr/bin/env python3
"""WP-E0 read-only inventory for JH-63 sample expand. Writes under runs/sample_expand_2026-09-25/wp-e0/."""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/tom/Documents/Git/alphaguard-wt-option-b")
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.contracts.events import TICKER_UNIVERSE
from alphaguard.ml.dataset_asof import default_yfinance_closes
from alphaguard.ml.dataset_ingest import (
    ARCHIVE_ALIAS_REGISTRY,
    FORBIDDEN_PRICE_FETCH_TICKERS,
    _apply_archive_aliases,
    _require_columns,
    normalize_headline,
    parse_calendar_date,
)

OUT = ROOT / "runs/sample_expand_2026-09-25/wp-e0"
OUT.mkdir(parents=True, exist_ok=True)

FREEZE = ROOT / "data/derived/training_events_optionB_001856a6.parquet"
RAW_DIR = ROOT / "data/raw/kaggle_stock_news"
SERVED = frozenset({"AAPL", "AMZN", "GOOGL", "META", "NVDA", "QQQ"})  # freeze-present
K = 100
MIN_HEADLINES = 200
# Dev-block window from 001856a6 80/20 (train idx 0..7124)
DEV_START = date(2011, 3, 2)
DEV_END = date(2020, 2, 25)
FREEZE_END = date(2020, 6, 10)
HISTORY_START = date(2008, 1, 1)
HISTORY_END = date(2021, 6, 1)
GIT_SHA = "1f53808d0945bab0b7a3119a9ee00ab524df6145"
FREEZE_HASH = "001856a6"


def load_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    df = _require_columns(raw)
    missing = df["date"].isna() | df["stock"].isna() | df["headline"].isna()
    missing |= df["headline"].astype(str).str.strip().eq("")
    df = df.loc[~missing].copy()
    df["ticker"] = df["stock"].astype(str).str.strip().str.upper()
    df["ticker"], applied, candidates, version = _apply_archive_aliases(
        df["ticker"], apply_archive_aliases=True
    )
    df["calendar_date"] = df["date"].map(parse_calendar_date)
    df = df.loc[df["calendar_date"].notna()].copy()
    df["normalized_headline"] = df["headline"].astype(str).map(normalize_headline)
    before = len(df)
    df = df.drop_duplicates(
        subset=["ticker", "calendar_date", "normalized_headline"], keep="first"
    )
    meta = {
        "path": str(path),
        "rows_raw": int(len(raw)),
        "rows_after_clean": before,
        "rows_after_dedup": int(len(df)),
        "alias_applied": applied,
        "alias_version": version,
    }
    return df, meta


def freeze_profile(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["feature_as_of"] = pd.to_datetime(df["feature_as_of"])
    df = df.sort_values(["feature_as_of", "event_id"]).reset_index(drop=True)
    td = df.groupby(["ticker", "feature_as_of"]).size().reset_index(name="n_rows")
    multi = td.loc[td["n_rows"] > 1]
    rows_in_repeated = int(multi["n_rows"].sum())
    train = df.iloc[:7125]
    test = df.iloc[7125:]
    td_pos = (
        df.assign(pos=df["label_high_risk"].astype(bool))
        .groupby(["ticker", "feature_as_of"])["pos"]
        .max()
        .reset_index()
    )
    per_ticker = {}
    for t, g in df.groupby("ticker"):
        tdu = int(g.groupby("feature_as_of").ngroups)
        pos_td = int(g.groupby("feature_as_of")["label_high_risk"].max().sum())
        per_ticker[t] = {
            "rows": int(len(g)),
            "unique_ticker_days": tdu,
            "pos_rows": int(g["label_high_risk"].sum()),
            "pos_ticker_days": pos_td,
        }
    # expanding4-ish fold positives on train block (equal time quartiles of train)
    train_asof = train["feature_as_of"]
    qs = [train_asof.quantile(q) for q in (0.25, 0.5, 0.75, 1.0)]
    fold_bounds = [train_asof.min()] + qs
    fold_pos = []
    for i in range(4):
        lo, hi = fold_bounds[i], fold_bounds[i + 1]
        if i < 3:
            mask = (df["feature_as_of"] >= lo) & (df["feature_as_of"] < hi)
        else:
            mask = (df["feature_as_of"] >= lo) & (df["feature_as_of"] <= hi) & (
                df.index < 7125
            )
        sub = df.loc[mask]
        by_t = (
            sub.loc[sub["label_high_risk"].astype(bool)]
            .groupby("ticker")
            .size()
            .to_dict()
        )
        fold_pos.append(
            {
                "fold": i,
                "asof_lo": str(pd.Timestamp(lo).date()),
                "asof_hi": str(pd.Timestamp(hi).date()),
                "n_rows": int(len(sub)),
                "n_pos_rows": int(sub["label_high_risk"].sum()),
                "pos_rows_by_ticker": {k: int(v) for k, v in by_t.items()},
            }
        )
    return {
        "git_sha": GIT_SHA,
        "freeze_hash_prefix": FREEZE_HASH,
        "freeze_path": str(FREEZE),
        "n_rows": int(len(df)),
        "n_unique_event_id": int(df["event_id"].nunique()),
        "n_unique_headline": int(df["headline"].nunique()),
        "n_tickers": int(df["ticker"].nunique()),
        "unique_ticker_days": int(len(td)),
        "unique_feature_as_of": int(df["feature_as_of"].nunique()),
        "singleton_ticker_day_groups": int((td["n_rows"] == 1).sum()),
        "multi_row_ticker_day_groups": int(len(multi)),
        "rows_in_repeated_ticker_day_groups": rows_in_repeated,
        "phase_c_7822_definition": (
            "rows belonging to (ticker, feature_as_of) groups with n_rows>=2; "
            f"Verified={rows_in_repeated}"
        ),
        "ticker_day_rows_describe": {
            "mean": float(td["n_rows"].mean()),
            "median": float(td["n_rows"].median()),
            "max": int(td["n_rows"].max()),
        },
        "pos_rows": int(df["label_high_risk"].sum()),
        "prevalence": float(df["label_high_risk"].mean()),
        "pos_ticker_days": int(td_pos["pos"].sum()),
        "distinct_dates_with_ge1_positive": int(
            df.loc[df["label_high_risk"].astype(bool), "feature_as_of"].nunique()
        ),
        "feature_as_of_min": str(df["feature_as_of"].min().date()),
        "feature_as_of_max": str(df["feature_as_of"].max().date()),
        "dev_block": {
            "n_rows": 7125,
            "n_pos": int(train["label_high_risk"].sum()),
            "asof_min": str(train["feature_as_of"].min().date()),
            "asof_max": str(train["feature_as_of"].max().date()),
            "unique_ticker_days": int(
                train.groupby(["ticker", "feature_as_of"]).ngroups
            ),
        },
        "locked_test": {
            "n_rows": 1782,
            "n_pos": int(test["label_high_risk"].sum()),
            "asof_min": str(test["feature_as_of"].min().date()),
            "asof_max": str(test["feature_as_of"].max().date()),
            "unique_ticker_days": int(
                test.groupby(["ticker", "feature_as_of"]).ngroups
            ),
            "anchor_feature_as_of": "2020-02-25",
        },
        "per_ticker": per_ticker,
        "approx_train_quartile_pos_by_ticker": fold_pos,
        "status": "Verified",
    }


def closes_ok(ticker: str) -> tuple[bool, str]:
    if ticker in FORBIDDEN_PRICE_FETCH_TICKERS:
        return False, "forbidden_archive_symbol"
    try:
        s = default_yfinance_closes(ticker, HISTORY_START, HISTORY_END)
    except Exception as e:  # noqa: BLE001
        return False, f"fetch_error:{type(e).__name__}:{e}"
    if s is None or len(s) == 0:
        return False, "empty_series"
    idx = pd.to_datetime(s.index)
    # Normalize tz-naive dates
    first = idx.min().date() if hasattr(idx.min(), "date") else pd.Timestamp(idx.min()).date()
    last = idx.max().date() if hasattr(idx.max(), "date") else pd.Timestamp(idx.max()).date()
    if first > date(2011, 4, 15):
        return False, f"starts_too_late:{first}"
    if last < date(2020, 5, 15):
        return False, f"ends_too_early:{last}"
    if len(s) < 1500:
        return False, f"too_few_bars:{len(s)}"
    return True, f"ok:n={len(s)}:{first}→{last}"


def main() -> None:
    print("=== freeze profile ===", flush=True)
    freeze = pd.read_parquet(FREEZE)
    fp = freeze_profile(freeze)
    (OUT / "freeze_profile.json").write_text(json.dumps(fp, indent=2) + "\n")
    print(
        "unique_ticker_days",
        fp["unique_ticker_days"],
        "rows_in_repeated",
        fp["rows_in_repeated_ticker_day_groups"],
        flush=True,
    )

    print("=== archive load (processed) ===", flush=True)
    processed_path = RAW_DIR / "analyst_ratings_processed.csv"
    partner_path = RAW_DIR / "raw_partner_headlines.csv"
    proc, proc_meta = load_csv(processed_path)
    print("processed dedup", proc_meta["rows_after_dedup"], flush=True)

    print("=== partner load ===", flush=True)
    partner, partner_meta = load_csv(partner_path)
    print("partner dedup", partner_meta["rows_after_dedup"], flush=True)

    # Archive profile post-alias post-dedup on primary (processed) — matches Option B build source
    g = (
        proc.groupby("ticker")
        .agg(
            rows=("headline", "size"),
            headline_days=("calendar_date", "nunique"),
            date_min=("calendar_date", "min"),
            date_max=("calendar_date", "max"),
        )
        .reset_index()
        .sort_values("rows", ascending=False)
    )
    # Dev-window counts
    in_dev = (proc["calendar_date"] >= DEV_START) & (proc["calendar_date"] <= DEV_END)
    dev_counts = (
        proc.loc[in_dev]
        .groupby("ticker")
        .agg(dev_rows=("headline", "size"), dev_headline_days=("calendar_date", "nunique"))
        .reset_index()
    )
    g = g.merge(dev_counts, on="ticker", how="left")
    g["dev_rows"] = g["dev_rows"].fillna(0).astype(int)
    g["dev_headline_days"] = g["dev_headline_days"].fillna(0).astype(int)
    g["date_min"] = g["date_min"].astype(str)
    g["date_max"] = g["date_max"].astype(str)
    g.to_csv(OUT / "archive_profile.csv", index=False)

    # Partner coverage for 6 served
    partner_served = {}
    for t in sorted(SERVED):
        sub = partner.loc[partner["ticker"] == t]
        partner_served[t] = {
            "dedup_rows": int(len(sub)),
            "headline_days": int(sub["calendar_date"].nunique()) if len(sub) else 0,
            "date_min": str(sub["calendar_date"].min()) if len(sub) else None,
            "date_max": str(sub["calendar_date"].max()) if len(sub) else None,
        }
    # Also SPY/MSFT for honesty
    for t in ("SPY", "MSFT"):
        sub = partner.loc[partner["ticker"] == t]
        partner_served[t] = {
            "dedup_rows": int(len(sub)),
            "headline_days": int(sub["calendar_date"].nunique()) if len(sub) else 0,
            "date_min": str(sub["calendar_date"].min()) if len(sub) else None,
            "date_max": str(sub["calendar_date"].max()) if len(sub) else None,
        }

    archive_stats = {
        "primary_source": proc_meta,
        "partner_source": partner_meta,
        "n_tickers_post_dedup": int(g["ticker"].nunique()),
        "total_dedup_rows": int(g["rows"].sum()),
        "tickers_ge200_dev": int((g["dev_rows"] >= MIN_HEADLINES).sum()),
        "partner_served_coverage": partner_served,
        "alias_registry": [
            {"rule_id": r.rule_id, "from": r.archive_symbol, "to": r.universe_ticker}
            for r in ARCHIVE_ALIAS_REGISTRY
        ],
        "forbidden_price_fetch": sorted(FORBIDDEN_PRICE_FETCH_TICKERS),
        "universe_contract": sorted(TICKER_UNIVERSE),
        "served_present_in_freeze": sorted(SERVED),
    }
    (OUT / "archive_filter_stats.json").write_text(
        json.dumps(archive_stats, indent=2) + "\n"
    )
    print(
        "tickers_ge200_dev",
        archive_stats["tickers_ge200_dev"],
        "n_tickers",
        archive_stats["n_tickers_post_dedup"],
        flush=True,
    )

    # Candidate rule (G2 locked): ≥200 dev-window headlines, closes OK, top K=100 + 6 served
    eligible = g.loc[g["dev_rows"] >= MIN_HEADLINES].sort_values(
        "dev_rows", ascending=False
    )
    print(
        f"=== closes probe for {len(eligible)} ge200 candidates (ranked) ===",
        flush=True,
    )
    closes_results = []
    kept_extra: list[str] = []
    dropped: list[dict] = []
    for i, row in enumerate(eligible.itertuples(index=False), 1):
        t = row.ticker
        ok, reason = closes_ok(t)
        rec = {
            "ticker": t,
            "dev_rows": int(row.dev_rows),
            "dev_headline_days": int(row.dev_headline_days),
            "all_rows": int(row.rows),
            "all_headline_days": int(row.headline_days),
            "closes_ok": ok,
            "closes_reason": reason,
            "served": t in SERVED,
        }
        closes_results.append(rec)
        if ok:
            if t not in SERVED:
                kept_extra.append(t)
        else:
            dropped.append(rec)
        if i % 25 == 0:
            print(
                f"  probed {i}/{len(eligible)}; extras_ok={len(kept_extra)} dropped={len(dropped)}",
                flush=True,
            )
        # Early stop once we have plenty beyond K (still finish ranking survivors)
        # Continue through all ge200 so survivorship_drop is complete.

    # Top K extras with closes + always include 6 served (even if served fail closes — they shouldn't)
    extras_ok = [r["ticker"] for r in closes_results if r["closes_ok"] and not r["served"]]
    top_extras = extras_ok[:K]
    # Served that pass closes
    served_ok = [r["ticker"] for r in closes_results if r["closes_ok"] and r["served"]]
    served_missing_from_eligible = sorted(SERVED - set(eligible["ticker"]))
    # Force-include served even if <200 (they are in freeze); probe them if missing
    for t in sorted(SERVED):
        if t not in {r["ticker"] for r in closes_results}:
            ok, reason = closes_ok(t)
            closes_results.append(
                {
                    "ticker": t,
                    "dev_rows": int(
                        g.loc[g["ticker"] == t, "dev_rows"].iloc[0]
                        if (g["ticker"] == t).any()
                        else 0
                    ),
                    "dev_headline_days": int(
                        g.loc[g["ticker"] == t, "dev_headline_days"].iloc[0]
                        if (g["ticker"] == t).any()
                        else 0
                    ),
                    "all_rows": int(
                        g.loc[g["ticker"] == t, "rows"].iloc[0]
                        if (g["ticker"] == t).any()
                        else 0
                    ),
                    "all_headline_days": int(
                        g.loc[g["ticker"] == t, "headline_days"].iloc[0]
                        if (g["ticker"] == t).any()
                        else 0
                    ),
                    "closes_ok": ok,
                    "closes_reason": reason,
                    "served": True,
                }
            )
            if ok:
                served_ok.append(t)
            else:
                dropped.append(closes_results[-1])

    candidate_set = sorted(set(top_extras) | set(served_ok) | set(SERVED))
    # Projected ticker-days: sum of unique headline days in freeze full window for candidate set
    in_freeze_win = (proc["calendar_date"] >= DEV_START) & (
        proc["calendar_date"] <= FREEZE_END
    )
    in_dev_win = (proc["calendar_date"] >= DEV_START) & (proc["calendar_date"] <= DEV_END)
    proj = proc.loc[in_freeze_win & proc["ticker"].isin(candidate_set)]
    proj_td = int(proj.groupby(["ticker", "calendar_date"]).ngroups)
    proj_dev = proc.loc[in_dev_win & proc["ticker"].isin(candidate_set)]
    proj_dev_td = int(proj_dev.groupby(["ticker", "calendar_date"]).ngroups)
    current_td = fp["unique_ticker_days"]
    s1_tickers = len([t for t in candidate_set if t not in SERVED]) + len(SERVED)
    # Distinct usable archive tickers under rule = extras with closes + served
    usable_count = len(set(top_extras) | set(SERVED))
    s1_fail_tickers = usable_count < 30
    s1_fail_td = proj_td < (3 * current_td)
    s1_stop = s1_fail_tickers or s1_fail_td

    candidates = {
        "rule": {
            "g2_locked": True,
            "min_dev_headlines": MIN_HEADLINES,
            "dev_window": [str(DEV_START), str(DEV_END)],
            "closes_required": True,
            "history_probe": [str(HISTORY_START), str(HISTORY_END)],
            "K": K,
            "plus_served": sorted(SERVED),
            "rank_by": "dev_rows desc",
        },
        "n_ge200_dev_pre_closes": int(len(eligible)),
        "n_closes_ok_extras": len(extras_ok),
        "n_top_K_extras": len(top_extras),
        "n_served_closes_ok": len(set(served_ok)),
        "candidate_tickers": candidate_set,
        "top_K_extras": top_extras,
        "served": sorted(SERVED),
        "projected_unique_ticker_days_freeze_window": proj_td,
        "projected_unique_ticker_days_dev_window": proj_dev_td,
        "current_unique_ticker_days": current_td,
        "ratio_vs_current": round(proj_td / current_td, 3) if current_td else None,
        "usable_ticker_count_under_rule": usable_count,
        "S1": {
            "distinct_usable_lt_30": s1_fail_tickers,
            "projected_td_lt_3x": s1_fail_td,
            "STOP": s1_stop,
            "threshold_td": 3 * current_td,
            "usable_count": usable_count,
            "projected_td": proj_td,
        },
        "status": "Verified",
    }
    (OUT / "candidate_tickers.json").write_text(json.dumps(candidates, indent=2) + "\n")
    (OUT / "survivorship_drop.json").write_text(
        json.dumps(
            {
                "n_ge200_probed": len(eligible),
                "n_dropped_no_closes": len([d for d in dropped if not d.get("served")]),
                "dropped": dropped,
                "closes_probe_all_ge200": closes_results,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "usable",
        usable_count,
        "proj_td",
        proj_td,
        "3x",
        3 * current_td,
        "S1_STOP",
        s1_stop,
        flush=True,
    )
    print("DONE core inventory", flush=True)


if __name__ == "__main__":
    main()
