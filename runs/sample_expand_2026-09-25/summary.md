# JH-63 Sample Expand — rollup (WP-E0 → WP-E4) · E4 FAIL

**Status:** COMPLETE docs (WP-E5) · **S5 STOP / FAIL** · **Model Quality Go: UNCLAIMED**  
**Date:** 2026-09-25 ~4:30 PM CT  
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b` @ `1f53808` (never option-a)  
**Plan:** `docs/plans/2026-09-25_jh63_sample_expand_strategy_plan.md`  
**Uncommitted:** leave uncommitted (Tom has not said commit)

## Claims discipline

- Harness `promotion_decision=rejected` ≠ Model Quality Go.
- **Go UNCLAIMED.** Fail stays Fail. Prior Fail results on freeze `534a341a…` and `001856a6…` remain Fail.
- No shopping: no floor change, no feature swap, no volume, no ticker-rule re-pick, no grid change, no re-run.
- **Next:** none, unless Tom authorizes a *new* pre-registered slice.

## Freeze lineage

| Freeze | Path / hash | n | Role |
|---|---|---:|---|
| Served baseline (Option B) | `training_events_optionB_001856a6.parquet` · study `001856a6…` | 8907 | Pre-expand Fail |
| Expanded (this slice) | `data/derived/training_events_jh63e_ecb73eca.parquet` · file `ecb73eca…` · study `2e8db9a9…` | **201255** | NEW8 train universe |
| Served rows in NEW8 | same 8907 `event_id`s / 1506 pos | 8907 | G3 primary eval slice |

Primary Go population (G3): **served_universe locked-test** under date-anchor = **1788** rows / **233** pos (contains the prior 1782 locked-test event_ids + 6 same-asof served rows). Floors unchanged: F1 ≥ 0.30 · P ≥ 0.25 · AUPRC ≥ 0.18 — all three per seed.

## Rollup E0 → E4

| WP | Result | One-line |
|---|---|---|
| **E0** | S1 **CLEAR** | Effective-n = **2826** ticker-days (not 8907 rows). G2 locked top-K=100 + 6 served = **106** usable tickers; projected ~30.7× ticker-days. Survivorship drop 881 (no closes). |
| **E1** | S2 variance-dominated · S3 **SIGNIFICANT** (p=0.0100) | Nested val AUPRC 0.413; G4 → E2 ALLOWED. |
| **E2** | Build COMPLETE · strict S4 bit-identity **FAIL** | NEW8 n=201255 (served 8907 / non-served 192348); 0 NaN; FinBERT MPS. Served event_ids + labels exact; **9-feature floats not bit-identical** (max\|Δ\| ~1e-5). |
| **E3** | COMPLETE | Cloned nested + WF configs to `*_2e8db9a9.yaml`; date-anchor split; G3 served-primary glue. |
| **E4** | **S5 FAIL** | Nested seeds 42/7/123 **all FAIL** floors. WF 0–4 report-only, also below. |

Per-WP detail: `runs/sample_expand_2026-09-25/wp-e{0,1,2,3,4}/summary.md`.

## S4 — float-tolerance (Tom decision path)

Plan S4 required served rows identical to `001856a6` (event_id + 9 features + label). E2 tripped on **float payloads**, not membership:

- n, `event_id` set, `label_high_risk`, prevalence, calendars, headlines: **exact**.
- All 9 features + `fwd_return_5d`: near-universal non-bit-identical floats; correlations ≈ 1.0; no FinBERT sign flips; label threshold never crossed.
- Causes (Verified probes): FinBERT rescoring numeric drift (MPS and CPU both ≠ old floats ~1e-6) + yfinance adjusted-close refresh.

**Decision:** Tom skipped the next-step widget. Parent defaulted to **float-tolerance PASS** (no splice of freeze columns onto served rows) and proceeded E3→E4. Strict bit-identity S4 remains documented as FAIL in `wp-e2/summary.md`. This rollup does not redefine S4 as a builder PASS under float tolerance — it records the authorized proceed path.

## E4 FAIL table (primary = served locked-test)

Config: `configs/studies/jh63_go_gate_nested_purge_2e8db9a9.yaml` · seeds 42/7/123 · purge-aligned · walk_forward=off.

| Seed | F1 | P | AUPRC | n_test | n_pos | Verdict |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 7 | 0.2488 | 0.1421 | 0.1572 | 1788 | 233 | **FAIL** (F1, P, AUPRC) |
| 42 | 0.2460 | 0.1403 | 0.1648 | 1788 | 233 | **FAIL** (F1, P, AUPRC) |
| 123 | 0.2467 | 0.1407 | 0.2031 | 1788 | 233 | **FAIL** (F1, P) |

**Nested Go verdict: FAIL.** Precision is the precision wall (~0.14 vs floor 0.25). F1 ≈ 0.25.

WF expanding4 (report-only, seeds 0–4): served F1 0.26–0.28, P 0.15–0.16 — below floors. Full-universe nested F1 ≈ 0.48 is **not** the Go population (G3); do not promote on it.

### Side-by-side (served nested; disk artifacts, no re-run)

| Seed | 534a F1/P/AUPRC | 001856a6 F1/P/AUPRC | 2e8db9a9 served F1/P/AUPRC |
| ---: | --- | --- | --- |
| 42 | 0.2528/0.1777/0.1829 | 0.0951/0.0806/0.1321 | 0.2460/0.1403/0.1648 |
| 7 | 0.2923/0.1931/0.1784 | 0.1793/0.1263/0.1349 | 0.2488/0.1421/0.1572 |
| 123 | 0.2574/0.1641/0.1703 | 0.1467/0.1006/0.1525 | 0.2467/0.1407/0.2031 |

NEW8 served nested beats `001856a6` on every seed (F1 ~0.25 vs 0.10–0.18) and lands near 534a F1 — still **below floors**, especially precision. Same failure mode. Fail stands.

## Story (public voice)

Sample expand attacked ticker-day starvation: 106 names, ~201k rows, ~30× projected ticker-days vs the 6-name freeze. E1 said more rows of this kind could help (variance-dominated + permutation significant). The build landed. The Go gate did not. Served locked-test precision stayed ~0.14. Expanding the training universe did not clear the pre-registered floors. That is the result.

## STOP / anti-shopping

- S5: any seed FAIL → Fail stands. Nested **42 / 7 / 123 all FAIL**.
- No re-runs, no volume features, no floor changes, no CloudAgent, no Dependabot in this slice.
- Serving `TICKER_UNIVERSE` contract untouched. Canonical `001856a6` / `534a` freezes not overwritten.
- Option-a checkout not used.

## Next

**none** — unless Tom starts a new pre-registered slice.

## Artifact index

| Item | Path |
|---|---|
| This rollup | `runs/sample_expand_2026-09-25/summary.md` |
| E0–E4 summaries | `runs/sample_expand_2026-09-25/wp-e0/` … `wp-e4/` |
| NEW8 parquet | `data/derived/training_events_jh63e_ecb73eca.parquet` |
| Nested study | `artifacts/runs/studies/jh63_go_gate_nested_purge_2e8db9a9/` |
| WF study | `artifacts/runs/studies/jh63_wf_expanding4_2e8db9a9/` |
| EXPERIMENTS | `docs/EXPERIMENTS.md` §11 |
| TRAINING_DATA | `docs/TRAINING_DATA.md` (training-universe section) |
| Backlog mirror | `~/Documents/Git/custom_resumes/docs/backlog/2026-09-25_jh63_sample_expand_e4_fail_summary.md` |
