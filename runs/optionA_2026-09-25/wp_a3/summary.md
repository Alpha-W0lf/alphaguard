# WP-A3: Prevalence vs floor feasibility

- **Verdict:** PASS
- **Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
- **Script:** `scripts/option_a/run_option_a.py (executor inline 2026-09-25)`

## Null baselines (locked_test prevalence = 0.1308)

- Random-classifier AUPRC ≈ prevalence = **0.1308**
- Constant-positive F1 = **0.2313**
- Prior-only (per-ticker base rate) AUPRC = **0.1547**
- Lift over null required for AUPRC ≥ 0.18: **1.377x**

### Noise-band flag: YES

AUPRC floor 0.18 is 1.38x locked_test prevalence 0.1308 (n=1782). Flag if floor sits near prevalence noise band on this sample size.

## Per-seed statements (existing FAIL artifacts only)

- Seed 42: locked_test AUPRC 0.2087 vs prevalence null 0.1308 (lift 1.596x); floor 0.18 needs lift 1.377x. F1=0.3658 (floor 0.30 met); P=0.2787 (floor 0.25 met).
- Seed 7: locked_test AUPRC 0.1946 vs prevalence null 0.1308 (lift 1.488x); floor 0.18 needs lift 1.377x. F1=0.2664 (floor 0.30 missed); P=0.1711 (floor 0.25 missed).
- Seed 123: locked_test AUPRC 0.1963 vs prevalence null 0.1308 (lift 1.501x); floor 0.18 needs lift 1.377x. F1=0.3227 (floor 0.30 met); P=0.2263 (floor 0.25 missed).
- Purge-on WF seed 0: AUPRC 0.1945 (lift 1.487x vs null); F1=0.2489; P=0.1452. Source `runs/phaseb_phasec_2026-09-25/seed0/run.json`.
- Purge-on WF seed 1: AUPRC 0.1676 (lift 1.282x vs null); F1=0.2347; P=0.1366. Source `runs/phaseb_phasec_2026-09-25/seed1/run.json`.
- Purge-on WF seed 2: AUPRC 0.1597 (lift 1.221x vs null); F1=0.2408; P=0.1397. Source `runs/phaseb_phasec_2026-09-25/seed2/run.json`.
- Purge-on WF seed 3: AUPRC 0.1670 (lift 1.277x vs null); F1=0.2465; P=0.1527. Source `runs/phaseb_phasec_2026-09-25/seed3/run.json`.
- Purge-on WF seed 4: AUPRC 0.1727 (lift 1.321x vs null); F1=0.2451; P=0.1498. Source `runs/phaseb_phasec_2026-09-25/seed4/run.json`.

## Artifacts

- `runs/optionA_2026-09-25/wp_a3/prevalence_floors.json`
- `runs/optionA_2026-09-25/wp_a3/null_baselines.csv`
- `runs/optionA_2026-09-25/wp_a3/summary.md`
