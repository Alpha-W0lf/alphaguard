# WP-A1: Residual leakage beyond C3

- **Verdict:** PASS_WITH_FLAG
- **Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
- **Script:** `scripts/option_a/run_option_a.py (executor inline 2026-09-25)`
- **Label:** `fwd_return_5d < -0.03` (unchanged)

## Same-ticker label-window overlaps

| split | purge_off | purge_on |
| --- | ---: | ---: |
| fold_0 | 6 | 0 |
| fold_1 | 5 | 0 |
| fold_2 | 26 | 0 |
| fold_3 | 70 | 0 |
| nested_locked_test | 92 | 0 (counterfactual) |

- Purge-on WF total same-ticker overlaps: **0** (pass requires 0).
- Nested Go-gate (`walk_forward=off`) same-ticker overlaps: **92** tickers=['GOOGL', 'META', 'NVDA', 'QQQ'].
- Nested counterfactual trading-day purge: train_end 7125→7029; overlaps → 0.

## Headline cross-split duplicates (normalized sha256)

- Nested shared hashes: **14** (flag if > 0).

## Question: did pre-purge Phase B benefit from leakage?

Purge-off WF and nested paths show non-zero same-ticker label-window overlaps; purge-on WF is zero. Worse purge-on Phase B scores are consistent with a pre-purge leakage benefit, but do not prove it (overlap counts Verified; causal claim Unverified).

## Artifacts

- `runs/optionA_2026-09-25/wp_a1/overlaps.json`
- `runs/optionA_2026-09-25/wp_a1/overlaps.csv`
- `runs/optionA_2026-09-25/wp_a1/summary.md`
