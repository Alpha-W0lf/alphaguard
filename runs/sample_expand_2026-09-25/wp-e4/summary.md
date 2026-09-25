# WP-E4 — Pre-registered acceptance (NEW8 `2e8db9a9`)

**Status:** COMPLETE · **S5 STOP / FAIL** · Go **UNCLAIMED**
**Date:** 2026-09-25 ~4:28 PM CT
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b`
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)
**Routing:** Local Mac only · `OMP_NUM_THREADS=1` · `--workers 1`
**Uncommitted:** leave uncommitted (Tom has not said commit)

## Claims discipline

- Harness `promotion_decision=rejected` ≠ Model Quality Go.
- **Go UNCLAIMED.** Fail stays Fail. No re-run / feature swap / grid change.
- Primary verdict population = **served_universe locked-test** (G3): n=**1788** / pos=**233**.
- Floors: F1≥0.30 · P≥0.25 · AUPRC≥0.18 — all three must clear **per seed**.

## Artifacts

| Item | Path |
|---|---|
| This summary | `runs/sample_expand_2026-09-25/wp-e4/summary.md` |
| Nested log | `runs/sample_expand_2026-09-25/wp-e4/nested.log` |
| WF log | `runs/sample_expand_2026-09-25/wp-e4/wf.log` |
| Nested study | `artifacts/runs/studies/jh63_go_gate_nested_purge_2e8db9a9/` |
| WF study | `artifacts/runs/studies/jh63_wf_expanding4_2e8db9a9/` |
| E3 configs + diffs | `runs/sample_expand_2026-09-25/wp-e3/` |

## (a) Nested Go purge-aligned — FAIL all seeds

Config: `configs/studies/jh63_go_gate_nested_purge_2e8db9a9.yaml`
`split_policy=nested_time_aware_v1_date_anchor` · seeds 42/7/123 · walk_forward=off · economic=off.
Harness promotion: `rejected` · seeds_failed=[42, 7, 123].

| Seed | F1 | P | AUPRC | n_test | n_pos | Verdict | Failed floors |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 7 | 0.2488 | 0.1421 | 0.1572 | 1788 | 233 | **FAIL** | f1 (0.2488 < 0.30); precision (0.1421 < 0.25); auprc (0.1572 < 0.18) |
| 42 | 0.2460 | 0.1403 | 0.1648 | 1788 | 233 | **FAIL** | f1 (0.2460 < 0.30); precision (0.1403 < 0.25); auprc (0.1648 < 0.18) |
| 123 | 0.2467 | 0.1407 | 0.2031 | 1788 | 233 | **FAIL** | f1 (0.2467 < 0.30); precision (0.1407 < 0.25) |

**Nested Go verdict: FAIL** (need all three seeds clear all floors).

## (b) expanding4 WF purge-on — report only

Config: `configs/studies/jh63_wf_expanding4_2e8db9a9.yaml`
`--walk-forward expanding4` · seeds 0–4 · economic=off · promotion=none.

| Seed | Served F1 | Served P | Served AUPRC | n | WF mean F1 | vs floors |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.2802 | 0.1638 | 0.1594 | 1788 | 0.3149 | below |
| 1 | 0.2702 | 0.1569 | 0.1815 | 1788 | 0.3127 | below |
| 2 | 0.2566 | 0.1478 | 0.2221 | 1788 | 0.3126 | below |
| 3 | 0.2660 | 0.1540 | 0.1948 | 1788 | 0.3041 | below |
| 4 | 0.2584 | 0.1490 | 0.1797 | 1788 | 0.3096 | below |

WF locked-test served metrics remain below floors (esp. precision). Report-only; does not claim Go.

## (c) Secondary — full-universe locked-test (report-only)

Executor glue stores full locked-test as `metrics["test_all"]` when `served_universe` is present.

| Seed (nested) | Served F1 | Full F1 | Full n / pos |
| ---: | ---: | ---: | --- |
| 7 | 0.2488 | 0.4786 | 11893 / 3671 |
| 42 | 0.2460 | 0.4775 | 11893 / 3671 |
| 123 | 0.2467 | 0.4776 | 11893 / 3671 |

Full-universe F1 ≈0.48 is **not** the Go population (G3). Do not promote on it.

## (d) Side-by-side (disk artifacts; no re-run of old freezes)

Primary numbers are **served locked-test** for NEW8; 001856a6/534a freezes were served-only (n_test=1782).

| Seed | 534a F1/P/AUPRC | 001856a6 F1/P/AUPRC | 2e8db9a9 served F1/P/AUPRC |
| ---: | --- | --- | --- |
| 42 | 0.2528/0.1777/0.1829 | 0.0951/0.0806/0.1321 | 0.2460/0.1403/0.1648 |
| 7 | 0.2923/0.1931/0.1784 | 0.1793/0.1263/0.1349 | 0.2488/0.1421/0.1572 |
| 123 | 0.2574/0.1641/0.1703 | 0.1467/0.1006/0.1525 | 0.2467/0.1407/0.2031 |

Sources: `runs/optionB_2026-09-25/wp-b4/summary.md`;
`artifacts/runs/studies/jh63_go_gate_nested_purge_001856a6/`;
`artifacts/runs/studies/jh63_go_gate_nested_purge_2e8db9a9/`.

NEW8 served nested is **better than 001856a6** on every seed (F1 ~0.25 vs 0.10–0.18),
but still below 534a on F1/P for seeds 7/123 and **precision remains far below 0.25** — same failure mode. Fail stands.

## Schema / glue notes

- `eval_slices` **not in** `StudyMatrixConfig` (silently ignored if present) → **not added** to YAML.
- G3 glue: `test_served_mask` → primary `metrics["test"]` = served; `metrics["test_all"]` = full.
- Floors/grid/seeds/hparams unchanged from 001856a6 clones.

## STOP S5

Any seed FAIL → Fail stands. Nested seeds **42 / 7 / 123 all FAIL**.
**Model Quality Go: UNCLAIMED.** No shopping.

