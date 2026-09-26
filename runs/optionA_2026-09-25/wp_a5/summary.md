# Option A verdict draft (WP-A5) — for Opus review

**Status:** DRAFT ONLY · Go UNCLAIMED · Fail stays Fail
**Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
**Script:** `scripts/option_a/run_option_a.py (executor inline 2026-09-25)`
**Generated:** 2026-09-25T18:35:14Z

## Draft conclusion: **(a) Label/leakage IS binding** (candidate — not final)

Name the cause: the nested Go-gate path (`jh63_go_gate_phase_c_534a`, `walk_forward=off`) retains **same-ticker label-window overlaps** across the train/locked-test boundary that the trading-day purge would remove. Purge-on WF expanding4 shows **0** same-ticker overlaps (Verified, WP-A1). Nested purge-off overlaps are **92** on tickers ['GOOGL', 'META', 'NVDA', 'QQQ'] (Verified, WP-A1). Cross-split normalized headline duplicates also exist on nested (n=14; FLAG, WP-A1).

Proposed change for Tom (not applied): align the nested Go-gate with the trading-day purge used for WF (or an explicit same-ticker horizon purge), trimming train membership to the WP-A1 counterfactual `train_end=7029` (from n_dev=7125) before any Option B freeze. Relabel is **not** required to clear this specific leakage; purge alignment is.

### Claim labels

| claim | status | evidence |
| --- | --- | --- |
| Purge-on WF same-ticker overlaps = 0 | Verified | `runs/optionA_2026-09-25/wp_a1/overlaps.json` |
| Nested walk_forward=off same-ticker overlaps > 0 | Verified | same |
| Headline cross-split duplicates on nested > 0 | Verified | same |
| Pre-purge Phase B scores benefited from leakage | Unverified | Consistent with worse purge-on scores; not proven |
| Floors require lift over prevalence null | Verified | `runs/optionA_2026-09-25/wp_a3/prevalence_floors.json` |
| Near-threshold / cluster noise material | Verified (descriptive) | `runs/optionA_2026-09-25/wp_a2/epidemiology.json` |
| Seed 42 vs 7/123 error-slice drivers | Unknown | WP-A4 BLOCKED (no saved predictions) |
| Option B should unlock now | Unverified | Blocked on Tom gate after Opus review |

## Alternates considered

- **(b) NOT binding:** Rejected as draft leader because the actual FAIL Go-gate path still carries nested residual leakage the purge would clear. Floors were hit by seed 42 on that leaky path, so "floors feasible + label clean" is not established.
- **(c) Floors infeasible at this prevalence/n:** Plausible alternate if Tom decides leakage is secondary. Locked_test prevalence ≈ 0.1308; AUPRC floor 0.18 needs lift over null. Nested seed 42 cleared all floors; seeds 7/123 did not — sample-size/seed variance may dominate (Unknown without WP-A4). Noise-band flag=True.

## WP rollup

| WP | verdict | path |
| --- | --- | --- |
| A1 | PASS_WITH_FLAG | `runs/optionA_2026-09-25/wp_a1/` |
| A2 | PASS | `runs/optionA_2026-09-25/wp_a2/` |
| A3 | PASS | `runs/optionA_2026-09-25/wp_a3/` |
| A4 | BLOCKED | `runs/optionA_2026-09-25/wp_a4/` |

## Go claim

**Model Quality Go remains UNCLAIMED.** This draft does not re-label any Fail.

## Next

Opus reviews this draft, then Tom chooses: purge/relabel change, Option B, or floor review.
