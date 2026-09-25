# WP-E0 — Inventory & effective-n audit (read-only)

**Status:** COMPLETE · S1 **CLEAR** (no STOP) · Go **UNCLAIMED**  
**Date:** 2026-09-25 ~3:10 PM CT  
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b` (clean `main`, never option-a)  
**Git SHA:** `1f53808d0945bab0b7a3119a9ee00ab524df6145`  
**Freeze:** `data/derived/training_events_optionB_001856a6.parquet` · hash prefix `001856a6`  
**Gates locked by Tom (this session):** G1 yes · **G2 yes** (rule locked) · G3 yes · G4 no · G5 yes  
**STOP rules honored:** no E1+, no training, no feature adds, no floor changes, Go UNCLAIMED.

## Artifacts

| File | Path |
|---|---|
| This summary | `runs/sample_expand_2026-09-25/wp-e0/summary.md` |
| Freeze profile | `runs/sample_expand_2026-09-25/wp-e0/freeze_profile.json` |
| Archive profile | `runs/sample_expand_2026-09-25/wp-e0/archive_profile.csv` |
| Archive filter stats | `runs/sample_expand_2026-09-25/wp-e0/archive_filter_stats.json` |
| Candidate tickers (G2) | `runs/sample_expand_2026-09-25/wp-e0/candidate_tickers.json` |
| Survivorship drop | `runs/sample_expand_2026-09-25/wp-e0/survivorship_drop.json` |
| FinBERT throughput | `runs/sample_expand_2026-09-25/wp-e0/finbert_throughput.json` |
| Citations check | `runs/sample_expand_2026-09-25/wp-e0/citations_check.md` |
| Audit script (uncommitted) | `runs/sample_expand_2026-09-25/wp-e0/audit_sample_expand_e0.py` |
| Run log | `runs/sample_expand_2026-09-25/wp-e0/inventory_run.log` |

## 1. Freeze effective-n (Verified)

| Metric | Value | Status |
|---|---|---|
| Rows | 8907 | Verified |
| Unique `(ticker, feature_as_of)` **ticker-days** | **2826** | Verified |
| Unique `feature_as_of` dates | 1665 | Verified |
| Singleton ticker-day groups | 1085 | Verified |
| Multi-row ticker-day groups | 1741 | Verified |
| Rows in multi-row groups | **7822** | Verified — resolves Phase C “7822 repeated rows” = rows whose `(ticker, feature_as_of)` group has size ≥ 2 |
| Mean / median / max rows per ticker-day | 3.15 / 2 / 56 | Verified |
| Pos rows / prevalence | 1506 / 0.1691 | Verified |
| Pos ticker-days | 453 | Verified |
| Distinct dates with ≥1 positive | 324 | Verified |
| Dev block (idx 0..7124) | 7125 rows · 1273 pos · td=2464 · asof 2011-03-02→2020-02-25 | Verified |
| Locked test (idx ≥7125) | **1782 rows · 233 pos** · td=364 · asof 2020-02-25→2020-06-10 · anchor `2020-02-25` | Verified |

### Per ticker (freeze)

| Ticker | Rows | Ticker-days | Pos rows | Pos td | Train rows | Test rows |
|---|---:|---:|---:|---:|---:|---:|
| NVDA | 3124 | 1154 | 770 | 257 | (majority) | |
| QQQ | 2772 | 1057 | 257 | 98 | (majority) | |
| GOOGL | 1824 | 439 | 330 | 72 | 1470 | 354 |
| AAPL | 469 | 66 | 66 | 8 | **0** | **469** |
| META | 389 | 78 | 64 | 16 | 17 | 372 |
| AMZN | 329 | 32 | 19 | 2 | **0** | **329** |

**Honesty (Verified):** AAPL and AMZN contribute **zero** training rows under the 80/20 cut; META almost none. Train is dominated by NVDA+QQQ+GOOGL. Archive calendar coverage confirms AAPL/AMZN headlines only appear from 2020-03 / 2020-04 onward (test window).

Approx train-quartile pos mix (see `freeze_profile.json`): early folds are NVDA+QQQ-only; later folds add GOOGL — matches EXPERIMENTS.md gate-(b) regime starvation diagnosis.

## 2. Archive filter stats (Verified)

Primary source (matches Option B build): `analyst_ratings_processed.csv`

| Step | Count |
|---|---:|
| Raw rows | 1,400,469 |
| After clean | 1,397,890 |
| After alias+dedup `(ticker, calendar_date, norm_headline)` | **1,384,360** |
| Distinct tickers post-dedup | 6,191 |
| Alias applied | FB→META 389 · GOOG→GOOGL 1209 |
| Tickers with ≥200 **dev-window** headlines | **1,772** |

Partner file `raw_partner_headlines.csv` (separate; not primary ingest):

| Ticker | Partner dedup rows | Notes |
|---|---:|---|
| GOOGL | 176 | 2020-05→06 only |
| META | 53 | late window |
| AAPL | 32 | late |
| SPY | 14 | matches prior doc |
| AMZN / NVDA / QQQ / MSFT | 0 | |

Partner does **not** meaningfully extend the 6 served names inside the freeze train window.

## 3. Candidate rule (G2 **locked**) — proposal executed as locked inventory

**Rule (Tom G2 yes):** US-listed symbol with ≥200 deduped headline rows whose calendar dates fall in the `001856a6` **dev block** `[2011-03-02, 2020-02-25]`, yfinance adjusted closes available for history probe `[2008-01-01, 2021-06-01]` (never forbidden `FB`/`GOOG`), rank by `dev_rows` desc, take **top K=100** + the **6 served** names present in the freeze.

| Gate | Value | Status |
|---|---|---|
| ≥200-dev pre-closes | 1772 | Verified |
| Closes OK extras | **888** | Verified |
| Survivorship drop (no closes) | **881** (749 empty_series / delisted-ish · 133 starts_too_late) | Verified |
| Top-K extras kept | 100 | Verified |
| Served force-included | AAPL, AMZN, GOOGL, META, NVDA, QQQ | Verified |
| META closes probe | Fail `starts_too_late:2012-05-18` (IPO) — still included as served (freeze already builds META) | Verified |
| **Usable tickers under rule** | **106** (=100+6) | Verified |
| Projected unique ticker-days (freeze window) | **86,829** | Verified |
| Projected unique ticker-days (dev window) | 81,891 | Verified |
| Current unique ticker-days | 2,826 | Verified |
| Ratio vs current | **30.7×** | Verified |
| Candidate archive headline rows (all / dev) | ~201,255 / ~174,225 | Verified |

Top-10 extras by `dev_rows`: MU, EBAY, VZ, MRK, QCOM, JNJ, NFLX, ORCL, M, WFC. Full list in `candidate_tickers.json`.

### S1 STOP check

| Criterion | Threshold | Observed | Trip? |
|---|---|---|---|
| Distinct usable archive tickers | < 30 | **106** | No |
| Projected expanded training ticker-days | < 3× current (8478) | **86,829** | No |

**S1 = CLEAR. Do not STOP.** Proceed readiness for WP-E1 (not started here).

## 4. FinBERT throughput (Verified)

| Metric | Value |
|---|---|
| Machine | M2 Pro · CPU · `OMP_NUM_THREADS=1` |
| Model | `ProsusAI/finbert` · batch 32 · max_length 64 |
| 1000 headlines infer | **10.43 s** → **95.8 headlines/s** |
| Load | 1.37 s |
| Projected infer for candidate ~201k headlines | **~35 min** |
| Projected infer for candidate ~174k (dev) | **~30 min** |
| Full archive 1.38M (not proposed) | ~4.0 h |

E2 wall time also includes yfinance + as-of/label join (Unknown until build).

## 5. Citation / local-doc checks

See `citations_check.md`. Summary:

- Wiley AFML page, Saito/Rehmsmeier, Google ML imbalanced, Figueroa BMC, all listed sklearn URLs → **Confirmed**.
- SSRN abstracts 2326253 / 3104816 → Cloudflare 403 from agent; handles recognized, bodies unread → **Partially confirmed**.
- `QUALITY_STANDARD.md` at `second_brain/docs/workflow_os/rails/` → **Confirmed readable**.
- Prior backlog inventory `2026-09-24_jh63_3_sample_expand_inventory.md` → **Confirmed readable**.

## 6. What was *not* done (STOP compliance)

- WP-E1 learning curve / permutation — **not started** (await Job Hunt dispatch after this report).
- No E2+ code, no training, no feature adds, no floor changes.
- `TICKER_UNIVERSE` / serving contract untouched.
- Freeze parquet not overwritten; option-a checkout not used.
- Artifacts left **uncommitted** (plan handoff).

## 7. Handoff for Job Hunt / E1

1. S1 clear → E1 may proceed on freeze `001856a6` **dev block only**.
2. G2 locked candidate set is in `candidate_tickers.json` (106 names).
3. G4 reminder: if E1 shuffle/permutation p ≥ 0.05 → **do not build E2**.
4. Effective-n for diagnostics: use **2826 ticker-days** (not 8907 rows) as the independence unit.
