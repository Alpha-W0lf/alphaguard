# WP-B4 Acceptance runs

**Status:** FAIL (all nested seeds) · 2026-09-25 CT  
**Freeze:** `001856a6b70801edefb578c37687be1555269de852baf7794294f2a51bce2034` (n=8907)  
**Workers:** 1 (Darwin) · `OMP_NUM_THREADS=1`  
**Model Quality Go: UNCLAIMED**  
**Anti-shopping:** FAIL → stop. No new features invented.

## Floors (unchanged)
F1 ≥ 0.30 · Precision ≥ 0.25 · AUPRC ≥ 0.18 (all three must clear per seed).

## (a) Nested Go, purge-aligned (`walk_forward=off`)

Study: `artifacts/runs/studies/jh63_go_gate_nested_purge_001856a6/`  
Config: `configs/studies/jh63_go_gate_nested_purge_001856a6.yaml`  
n_train=7029, n_test=1782 on every seed (Verified).

| Seed | Test F1 | Test P | Test AUPRC | Verdict | Artifact |
| --- | --- | --- | --- | --- | --- |
| 42 | 0.0951 | 0.0806 | 0.1321 | **FAIL** (F1, P, AUPRC) | `artifacts/runs/studies/jh63_go_gate_nested_purge_001856a6/runs/run_000_2a42d7dc_s42.json` |
| 7 | 0.1793 | 0.1263 | 0.1349 | **FAIL** (F1, P, AUPRC) | `…/run_001_c035b7c8_s7.json` |
| 123 | 0.1467 | 0.1006 | 0.1525 | **FAIL** (F1, P, AUPRC) | `…/run_002_2ba2f1aa_s123.json` |

Harness: `promotion_decision=rejected`, `seeds_cleared=[]`, `seeds_failed=[42,7,123]` — Verified `study.json` / `compare.md`.

### XGB gain importance (9 features)

Verified via Booster `get_score(importance_type='gain')` on each seed bundle — `nested/xgb_gain.json`.

| Feature | seed 42 | seed 7 | seed 123 |
| --- | ---: | ---: | ---: |
| finbert_sentiment | 0.00 | 0.00 | 0.53 |
| volatility_20d | 94.22 | 89.68 | 97.99 |
| return_5d_prior | 56.22 | 47.89 | 54.89 |
| return_20d_prior | 43.85 | 49.80 | 44.87 |
| spy_return_5d | 47.09 | 45.45 | 45.67 |
| rs_20d | 81.68 | 83.76 | 80.60 |
| drawdown_20d | 63.12 | 86.35 | 47.14 |
| volatility_5d | 61.16 | 52.22 | 57.63 |
| spy_volatility_20d | 47.79 | 53.22 | 51.40 |

## Side-by-side: 534a clean nested vs 001856a6 clean nested

| Seed | 534a F1 | 534a P | 534a AUPRC | 534a | 001856a6 F1 | 001856a6 P | 001856a6 AUPRC | 001856a6 |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 42 | 0.2528 | 0.1777 | 0.1829 | FAIL | 0.0951 | 0.0806 | 0.1321 | FAIL |
| 7 | 0.2923 | 0.1931 | 0.1784 | FAIL | 0.1793 | 0.1263 | 0.1349 | FAIL |
| 123 | 0.2574 | 0.1641 | 0.1703 | FAIL | 0.1467 | 0.1006 | 0.1525 | FAIL |

534a paths: `runs/optionA_2026-09-25/purge_align/summary.md` (main checkout) / `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/`.  
001856a6 paths: this directory + study artifacts above.  
**534a Fail remains Fail historically.** Option B did not clear floors.

## (b) expanding4 WF, purge-on

Study: `artifacts/runs/studies/jh63_wf_expanding4_001856a6/`  
Config: `configs/studies/jh63_wf_expanding4_001856a6.yaml`  
Per-fold table: `expanding4/folds.md` / `fold_metrics.json`.

Locked-test F1 (brief): seed0=0.1773, seed1=0.1404, seed2=0.1979, seed3=0.1385, seed4=0.1667 — all below floors (promotion none). Compare to Phase B 534a purge-on locked-test F1 ≈0.25–0.30 (`runs/phaseb_2026-09-25/SUMMARY.md` on main checkout).

## Cross-split duplicate headlines (NOTE only; no dedupe)

Verified on new purge split (train_end=7029, test start=7125): **14** normalized-headline duplicates across sides; **7** ticker+headline duplicates. `nested/cross_split_dupes.json`. Plan does not authorize dedupe.

## Verdict
**FAIL.** Go UNCLAIMED. No feature shopping.
