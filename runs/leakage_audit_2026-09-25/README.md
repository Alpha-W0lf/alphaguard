# Leakage audit, 2026-09-25

The harness checked whether any training row's 5-day label window reaches into the next block, on the 8,907-event freeze `534a341a…` (the retired 5-feature freeze; see [`docs/EXPERIMENTS.md`](../../docs/EXPERIMENTS.md) §7).

## Same-ticker label-window overlaps

| Split | Before the purge | After the purge |
|---|---:|---:|
| Walk-forward fold 0 | 6 | 0 |
| Walk-forward fold 1 | 5 | 0 |
| Walk-forward fold 2 | 26 | 0 |
| Walk-forward fold 3 | 70 | 0 |
| Locked test | 92 | 0 |

On the locked-test boundary the trading-day purge moves the end of training from row 7,125 to row 7,029, so no training label window crosses into the test block.

## Files

| File | What it holds |
|---|---|
| `overlaps.csv` | The table above, per split, with the affected tickers |
| `overlaps.json` | Full per-fold detail, headline duplicates across splits (14) and the pass criteria |
| `purge_check.json` | The locked-test purge check: train 7,029 rows, test 1,782, overlaps 0, dataset hash matches the freeze |

`scripts/audit_phase_c.py` reruns the overlap check, among others, on a rebuilt freeze; its overlap output is `c3_leakage.json` under `--out` ([`docs/EXPERIMENTS.md`](../../docs/EXPERIMENTS.md) §7).

## Note, 2026-10-19

These records were moved here from their original folder. Internal labels were removed, one key was renamed (`wp_a1_…` → `audit_…`), the paths of the original run scripts were replaced (those scripts are not included; they are not this repo's `scripts/`), and two internal summaries were removed. Every number is unchanged.
