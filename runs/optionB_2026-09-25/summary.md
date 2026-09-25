# Option B summary — features + new freeze

**Status:** FAIL · COMPLETE WP-B0–B5 · 2026-09-25 CT  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b`  
**Branch:** `analysis/option-b-2026-09-25`  
**Base tip:** `71d6f5fe112627f35cc99950672f8577b3908920` (PR #19 purge-align + OpenMP)  
**Plan:** `docs/plans/2026-09-25_jh63_option_b_features_freeze_plan.md`

## Claims discipline
Every claim below is **Verified** unless marked otherwise.  
**Model Quality Go: UNCLAIMED** (regardless of harness `rejected`).  
**534a Fail remains Fail** in the historical record (`runs/optionA_2026-09-25/purge_align/summary.md`).

## Freeze
| Field | Value | Status |
| --- | --- | --- |
| Backup | `data/derived/training_events_jh633_534a341a.parquet` hash `534a341a…` | Verified WP-B0 |
| New hash | `001856a6b70801edefb578c37687be1555269de852baf7794294f2a51bce2034` | Verified WP-B2 |
| `<NEW8>` | `001856a6` | Verified |
| n | 8907 | Verified |
| Label prevalence | 0.16908049848433815 (n_pos=1506) identical to backup | Verified |
| FinBERT | exact-identical on 8907 `event_id` joins | Verified |
| NaN (9 features) | 0 | Verified |
| Features | original 5 + `rs_20d`, `drawdown_20d`, `volatility_5d`, `spy_volatility_20d` only | Verified |

## Pytest
Verified WP-B1: `187 passed, 1 skipped, 6 deselected` → after rebuild freeze test also green. Artifact: `wp-b1/pytest_full.txt`.

## Nested Go (WP-B4a) — FAIL all seeds
| Seed | F1 | P | AUPRC | n_train | n_test | Verdict |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 42 | 0.0951 | 0.0806 | 0.1321 | 7029 | 1782 | FAIL |
| 7 | 0.1793 | 0.1263 | 0.1349 | 7029 | 1782 | FAIL |
| 123 | 0.1467 | 0.1006 | 0.1525 | 7029 | 1782 | FAIL |

Artifacts: `artifacts/runs/studies/jh63_go_gate_nested_purge_001856a6/`, `wp-b4/nested/`.  
XGB gain: `wp-b4/nested/xgb_gain.json` (rs_20d / drawdown_20d / volatility_20d dominate; FinBERT ≈0).

## expanding4 WF (WP-B4b)
Per-fold: `wp-b4/expanding4/folds.md`. Locked-test F1 by seed: 0.1773 / 0.1404 / 0.1979 / 0.1385 / 0.1667 — below floors. Study: `jh63_wf_expanding4_001856a6`.

## Side-by-side vs 534a clean nested
Option B nested scores are **worse** than Option A clean nested on every seed (see `wp-b4/summary.md`). Fail stands.

## Cross-split headline dupes
14 normalized-headline dups across purge split (same count as Option A NOTE). No dedupe authorized. `wp-b4/nested/cross_split_dupes.json`.

## Anti-shopping
WP-B4 FAIL → **stopped**. No new features, no denser grid, no floor change.

## Decision gate (Tom)
Mixed/FAIL case: Fail stands. Choose floor review, park, or authorize a *new* pre-registered feature slice (e.g. volume). Grok does not iterate.

## Go
**UNCLAIMED.**
