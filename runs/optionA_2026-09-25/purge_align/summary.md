# JH63 nested purge-align — Go-gate re-run summary

**Status:** COMPLETE · 2026-09-25 CT · leave uncommitted  
**Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` (unchanged; no new parquet)  
**Model Quality Go: UNCLAIMED** (even though harness logged `promotion_decision=rejected`; Unverified-for-Go until Tom decides)

## What changed

`split_for_walk_forward` no longer early-returns to unpurged `time_ordered_split` when `walk_forward=off`. With session indices, both `off` and `expanding4` apply the locked-test trading-day purge (train_end **7029**, test start **7125**).

## Acceptance (Verified)

| Check | Result | Path |
| --- | --- | --- |
| Unit `tests/test_phase_c_audit.py` | 15 passed | — |
| Full `uv run pytest -q` | 177 passed, 6 deselected | — |
| One-shot purge align | train 7029, test start 7125, overlaps 0, freeze match | `runs/optionA_2026-09-25/purge_align/check.json` |
| Nested study | 3/3 completed, aborted=0 | `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/` |
| Old Phase C study mtime | unchanged (`2026-09-25 13:09:12` CT) | `artifacts/runs/studies/jh63_go_gate_phase_c_534a/` |
| Dataset hash | matches freeze on all 3 runs | run JSONs + `study.json` |

`check.json` key numbers (Verified): `n_train=7029`, `boundary_test_start=7125`, `n_test=1782`, `same_ticker_overlap_train_rows=0`, `prefix_end_before_session=7029`, `model_quality_go=UNCLAIMED`.

## Floors

F1 ≥ 0.30 · Precision ≥ 0.25 · AUPRC ≥ 0.18 (all must clear per seed). Source: `configs/studies/jh63_go_gate_nested_purge_534a.yaml` / `study.json` promotion_rollup.

## Per-seed metrics — NEW nested purge (`jh63_go_gate_nested_purge_534a`)

n_train=7029, n_test=1782 on every seed (Verified via `metrics.train.n_samples` / `metrics.test.n_samples` in run JSONs).

| Seed | Run | Test F1 | Test P | Test AUPRC | Floors | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| 42 | `run_000_41f8b861_s42` | 0.2528 | 0.1777 | 0.1829 | **FAIL** (F1, P) | `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/runs/run_000_41f8b861_s42.json` |
| 7 | `run_001_298f71da_s7` | 0.2923 | 0.1931 | 0.1784 | **FAIL** (F1, P, AUPRC) | `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/runs/run_001_298f71da_s7.json` |
| 123 | `run_002_510a5b3b_s123` | 0.2574 | 0.1641 | 0.1703 | **FAIL** (F1, P, AUPRC) | `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/runs/run_002_510a5b3b_s123.json` |

Harness: `promotion_decision=rejected`, `seeds_cleared=[]`, `seeds_failed=[42,7,123]` — Verified `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/study.json` and `compare.md`.  
**Model Quality Go: UNCLAIMED.**

## Old vs new (Phase C FAIL → nested purge)

Old Phase C (purge NOT applied under `walk_forward=off`; n_train effectively 7125). Source: `artifacts/runs/studies/jh63_go_gate_phase_c_534a/go_gate_summary.json`.

| Seed | Old F1 | New F1 | ΔF1 | Old P | New P | ΔP | Old AUPRC | New AUPRC | ΔAUPRC | Old floors | New floors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | 0.3658 | 0.2528 | −0.1130 | 0.2787 | 0.1777 | −0.1010 | 0.2087 | 0.1829 | −0.0258 | PASS | FAIL |
| 7 | 0.2664 | 0.2923 | +0.0259 | 0.1711 | 0.1931 | +0.0220 | 0.1946 | 0.1784 | −0.0162 | FAIL | FAIL |
| 123 | 0.3227 | 0.2574 | −0.0653 | 0.2263 | 0.1641 | −0.0622 | 0.1963 | 0.1703 | −0.0260 | FAIL | FAIL |

Old gate_overall: **FAIL** (`go_gate_summary.json`). New gate: **rejected** / all seeds fail floors. Leakage-aligned nested split does **not** clear Go floors.

## NOTE (not pass/fail for this change)

Cross-split shared normalized headline hashes = **14** (Verified `runs/optionA_2026-09-25/wp_a1/overlaps.json` → `headline_duplicates`). Do not dedupe headlines in this slice.

## Ops note

Study re-run used `--workers 1` plus `OMP_NUM_THREADS=1` / `XGB_NUM_THREAD=1` (not `--workers 2`) to avoid macOS Python SIGSEGV in libomp under the local-exec sandbox.

## Files touched (uncommitted)

- `src/alphaguard/ml/study_walkforward.py` — remove early return; mode ValueError; docstring
- `tests/test_phase_c_audit.py` — `off`-with-sessions assert
- `configs/studies/jh63_go_gate_nested_purge_534a.yaml` — new (study_id + description only vs Phase C)
- `scripts/option_a/nested_purge_align_check.py` — new one-shot
- `runs/optionA_2026-09-25/purge_align/check.json`
- `runs/optionA_2026-09-25/purge_align/summary.md`
- Artifacts: `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/` (new; Phase C dir untouched)

## Stop

Hand off to Job Hunt for Tom. No commit. Go UNCLAIMED.
