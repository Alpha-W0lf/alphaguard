# WP-A2: Label epidemiology and hard cases

- **Verdict:** PASS
- **Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
- **Script:** `scripts/option_a/run_option_a.py (executor inline 2026-09-25)`

## Near-threshold mass (`fwd_return_5d` vs −0.03)

| slice | ±0.5% share_all | ±0.5% share_pos | ±1% share_all | ±1% share_pos | selloff≥50% pos share |
| --- | ---: | ---: | ---: | ---: | ---: |
| fold_0 | 0.0421 | 0.0618 | 0.0946 | 0.1124 | 0.9719 |
| fold_1 | 0.0748 | 0.1833 | 0.1506 | 0.3200 | 0.9033 |
| fold_2 | 0.0393 | 0.1330 | 0.1347 | 0.4149 | 0.6915 |
| fold_3 | 0.0393 | 0.1297 | 0.0823 | 0.1946 | 0.9027 |
| locked_test | 0.0286 | 0.0601 | 0.0623 | 0.1159 | 0.7725 |

## fold_0 ticker positives

- NVDA positives in fold_0: **177** (0.9944 of fold_0 positives)
- Per-ticker: `{'NVDA': 177, 'QQQ': 1}`

## NVDA inheritance into later fold trains

| fold | train_pos | nvda_train | nvda_share | nvda_before_fold0_end | early_share |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 422 | 257 | 0.6090 | 257 | 0.6090 |
| 1 | 599 | 433 | 0.7229 | 433 | 0.7229 |
| 2 | 900 | 579 | 0.6433 | 434 | 0.4822 |
| 3 | 1083 | 649 | 0.5993 | 434 | 0.4007 |

## Artifacts

- `runs/optionA_2026-09-25/wp_a2/epidemiology.json`
- `runs/optionA_2026-09-25/wp_a2/fwd_return_histogram.csv`
- `runs/optionA_2026-09-25/wp_a2/nvda_inheritance.csv`
- `runs/optionA_2026-09-25/wp_a2/summary.md`
