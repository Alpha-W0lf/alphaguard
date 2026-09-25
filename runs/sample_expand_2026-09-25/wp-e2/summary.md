# WP-E2 — Training-universe ingest + builder

**Status:** COMPLETE build · **S4 STOP / FAIL** (served feature drift) · Go **UNCLAIMED**  
**Date:** 2026-09-25 ~4:08 PM CT  
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b` @ `1f53808` (never option-a)  
**Gates:** G1–G5 locked yes/yes/yes/no/yes (E1 cleared G4 path)  
**Uncommitted:** all code + artifacts (Tom has not said commit)

## Artifacts

| File | Path |
|---|---|
| This summary | `runs/sample_expand_2026-09-25/wp-e2/summary.md` |
| Build log | `runs/sample_expand_2026-09-25/wp-e2/build.log` |
| Drift audit | `runs/sample_expand_2026-09-25/wp-e2/s4_drift.json` |
| MPS smoke | `runs/sample_expand_2026-09-25/wp-e2/mps_smoke.json` |
| Pytest (touched) | `runs/sample_expand_2026-09-25/wp-e2/pytest_touched.txt` |
| Staging parquet | `data/derived/training_events_jh63e_building.parquet` |
| Named parquet | `data/derived/training_events_jh63e_ecb73eca.parquet` |

## Part A — MPS FinBERT

- `score_headlines` prefers MPS when `torch.backends.mps.is_available()`, else CPU; tensors moved to device; softmax → `.cpu().numpy()`; logs `FinBERT device=<cpu|mps> batch_size=N`; default `batch_size=16`; MPS errors fall back to CPU with warning.
- Smoke (32 headlines, batch 16, includes model load): **device=mps**, 5.30 s, ~6.0 headlines/s load-inclusive. E0 CPU infer-only baseline was ~95.8 h/s after load.
- Build log confirms: `FinBERT device=mps batch_size=16`.

## Part B — Code (uncommitted)

| File | Change |
|---|---|
| `src/alphaguard/ml/dataset_finbert.py` | MPS prefer + CPU fallback |
| `src/alphaguard/ml/dataset_ingest.py` | `training_universe: frozenset[str] \| None` (None = `TICKER_UNIVERSE`, byte-identical path) |
| `src/alphaguard/ml/dataset_build.py` | `--training-universe-file`, `served_universe` column, `--finbert-batch-size` |
| `src/alphaguard/ml/study_walkforward.py` | `nested_time_aware_v1_date_anchor` + `LOCKED_TEST_ASOF_ANCHOR_001856A6=2020-02-25` |
| `src/alphaguard/ml/study_executor.py` | Passes `config.split_policy` into split |
| `tests/test_dataset_build.py` | Universe None identity, alias+expand, served column, date-anchor, purge-across-tickers |

**Not edited:** `contracts/events.TICKER_UNIVERSE` / serving validators.

**Pytest:** `tests/test_dataset_build.py` + `test_contracts.py` + `test_phase_c_audit.py` → **44 passed** in 3.06 s.

## Part C — Build

```text
OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1
.venv/bin/python scripts/build_training_events.py \
  --skip-download --allow-shortfall --target-rows 500000 \
  --training-universe-file runs/sample_expand_2026-09-25/wp-e0/candidate_tickers.json \
  --finbert-batch-size 16 \
  --out data/derived/training_events_jh63e_building.parquet
```

| Metric | Value | Status |
|---|---|---|
| Ingest sampled | 201255 (dedup=universe after 106-ticker filter) | Verified |
| asof/label drop | **0** (`kept=201255 dropped_no_closes_or_label=0`) | Verified |
| Out rows | **201255** | Verified |
| Served / non-served | **8907** / 192348 | Verified |
| Tickers | 106 | Verified |
| NaN over 9 features | **0** | Verified |
| Parquet file sha256 | `ecb73ecae9b0704011345927cb05749aa6147e54dfb4d0f65d819740189a12cf` (`<file8>=ecb73eca`) | Verified |
| Study-style dataset_hash (full X+y) | `2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528` | Verified ≠ `001856a6` |
| Served-only X+y hash | `7b989bfd8961d570…` | ≠ freeze `001856a6b70801ed…` (drift cause) |
| FinBERT device | mps | Verified |
| Ollama | left running (not killed) | Note |

Date-anchor preview on new freeze (not used for S4 verdict): boundary idx 189362 → test 11893; served locked-test under date-anchor = **1788** rows / **233** pos (contains all 1782 old locked-test event_ids + 6 same-asof served rows that sat on the train side of the old 80/20 cut).

## Acceptance (a)–(f)

| ID | Check | Result |
|---|---|---|
| (a) | Served rows = `001856a6` exactly (event_id set **and** identical 9 features + label) | **FAIL** — event_id + label OK; **9 features not bit-identical** |
| (b) | Locked-test served slice = 1782 / 233 | Identity of old 1782 event_ids preserved in freeze; date-anchor served test expands to 1788/233 (see above). Not the S4 trip. |
| (c) | New dataset_hash ≠ `001856a6` | PASS (`2e8db9a9…` / file `ecb73eca…`) |
| (d) | 0 NaN over 9 features | PASS |
| (e) | rows by ticker / drops / prevalence reported | PASS — drop=0; served prev=0.16908 (= freeze); non-served prev=0.17841 (34317/192348) |
| (f) | Pytest green (touched + serving contracts) | PASS (44) |

## S4 STOP — served feature drift (do not paper over)

**Plan STOP S4:** *“Any n or prevalence drift on served rows → STOP, Tom.”* and acceptance (a) requires **identical 9 features + label**.

### What matches (exact)

| Field | Result |
|---|---|
| Served n | 8907 = freeze |
| `event_id` set | Equal (0 only-old / 0 only-new) |
| `label_high_risk` | 0 mismatches; positives **1506** = freeze |
| Served prevalence | 0.16908049848433815 = freeze |
| `feature_as_of` / `published_at` / headline / ticker / source hashes | Exact |

### What fails strict identity

Aligned on `event_id` (8907 rows). Counts of **non-bit-identical** floats:

| Column | n_mismatch | frac | max\|Δ\| | mean\|Δ\| | median\|Δ\| |
|---|---:|---:|---:|---:|---:|
| finbert_sentiment | 8857 | 0.994 | 3.4e-5 | 6.1e-7 | 2.3e-7 |
| volatility_20d | 8578 | 0.963 | 5.0e-6 | 7.9e-7 | 6.2e-7 |
| return_5d_prior | 8224 | 0.923 | 1.0e-6 | 2.1e-7 | 1.6e-7 |
| return_20d_prior | 8204 | 0.921 | 1.0e-6 | 2.2e-7 | 1.8e-7 |
| spy_return_5d | 8677 | 0.974 | 1.0e-6 | 2.6e-7 | 2.3e-7 |
| rs_20d | 8907 | 1.000 | 2.0e-6 | 3.5e-7 | 2.9e-7 |
| drawdown_20d | 6419 | 0.721 | 1.0e-6 | 1.5e-7 | 9.0e-8 |
| volatility_5d | 8578 | 0.963 | 1.6e-5 | 1.8e-6 | 1.4e-6 |
| spy_volatility_20d | 8907 | 1.000 | 4.0e-6 | 8.9e-7 | 7.0e-7 |
| fwd_return_5d | 8252 | 0.926 | 2.0e-6 | 2.1e-7 | 1.6e-7 |
| label_high_risk | **0** | 0 | 0 | 0 | 0 |

Correlations vs freeze are all ≈ **1.0000000000**. No FinBERT sign flips. Label threshold never crossed.

### Diagnosis (Verified probes)

1. **Not a row-set / join bug.** Event IDs, calendars, and labels match. S4 fails on **float payloads**, not membership.
2. **FinBERT MPS vs CPU (32 mismatched headlines re-scored):**
   - MPS scores **bit-match** the new freeze (`max|Δ|=0`).
   - MPS vs CPU max|Δ| ≈ **2.4e-6** (device numeric noise).
   - **Both** MPS and CPU differ from freeze `001856a6` FinBERT by ~**1e-6** max on the sample.
   - Conclusion: drift vs freeze is **not** “MPS alone corrupted scores.” Rescoring today (MPS or CPU) does not reproduce the old FinBERT floats bit-exactly (torch/transformers numeric path and/or prior build environment). MPS is confirmed as the device that wrote the new freeze.
3. **Price features / `fwd_return_5d`:** consistent with **yfinance adjusted-close refresh**. Builder always `yfinance cache miss: downloading …` (in-process cache only; full re-download of 106 + SPY). Yahoo adjusted history moves slightly over time → close-derived floats differ at 1e-7–1e-5 while labels stay put.
4. **Hash consequence:** served-only study hash moved `001856a6…` → `7b989bfd…` solely from these float deltas; parquet file named from **file** sha256 `ecb73eca…`.

### What was NOT done (STOP compliance)

- **No** float-tolerance redefinition of S4 PASS.
- **No** splicing freeze feature columns onto served rows.
- **No** WP-E3 config clones.
- **No** WP-E4 nested/WF runs.
- **No** floor / Go claims. Go **UNCLAIMED**.
- Option-a checkout untouched. Canonical `training_events.parquet` / `001856a6` not overwritten.

## Handoff for Tom

S4 is a **hard STOP**. Builder produced the expanded freeze (`n=201255`, served n/ids/labels intact) but **served 9-feature floats are not identical** to `001856a6`. Likely causes are (a) FinBERT rescoring numeric drift (MPS/CPU both ≠ old floats at ~1e-6) and (b) yfinance adjusted-close refresh. Next step is Tom’s call — executor will not proceed to E3/E4 from this state.
