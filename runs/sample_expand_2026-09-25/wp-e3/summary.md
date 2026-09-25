# WP-E3 — Study config clones (NEW8 `2e8db9a9`)

**Status:** COMPLETE  
**Date:** 2026-09-25 ~4:22 PM CT  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b`  
**S4 decision (Tom skipped widget):** float-tolerance PASS; no splice; proceed E3→E4.

## Cloned configs

| Target | Source |
|---|---|
| `configs/studies/jh63_go_gate_nested_purge_2e8db9a9.yaml` | `…_001856a6.yaml` |
| `configs/studies/jh63_wf_expanding4_2e8db9a9.yaml` | `…_001856a6.yaml` |

Diffs (attached):
- `runs/sample_expand_2026-09-25/wp-e3/diff_nested_go_gate.txt`
- `runs/sample_expand_2026-09-25/wp-e3/diff_wf_expanding4.txt`

### Allowed diffs only

| Field | New value |
|---|---|
| `study_id` | `jh63_*_2e8db9a9` |
| `description` | NEW8 / date-anchor / G3 note |
| `dataset_path` | `data/derived/training_events_jh63e_ecb73eca.parquet` |
| `dataset_hash` | `2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528` |
| `split_policy` | `nested_time_aware_v1_date_anchor` |

Grid / floors / seeds / hparams byte-identical otherwise.  
`534a` and `001856a6` configs left untouched.

## Schema blocker: `eval_slices`

`StudyMatrixConfig` (`src/alphaguard/ml/study_schema.py`) has **no** `eval_slices` field.
Pydantic silently ignores unknown keys (`extra` default), so putting
`eval_slices: [served_universe, all]` in YAML would be a no-op — **not added**.

Primary served metrics are produced by executor glue (below) and reported in WP-E4
`summary.md` without inventing unsupported YAML keys.

## G3 glue (minimum)

When parquet has `served_universe`, split carries `test_served_mask`; executor sets:

- `metrics["test"]` = **served** locked-test (primary floors / promotion)
- `metrics["test_all"]` = full locked-test (secondary report-only)

Smoke on NEW8: locked-test n=11893; served mask n=**1788** / pos=**233**.

Files touched: `train_option_b.py` (SplitData field), `study_walkforward.py` (mask),
`study_executor.py` (primary slice). Floors/grid unchanged.
