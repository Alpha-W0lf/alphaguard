# WP-E1 summary — sample expand gate

**Date:** 2026-09-25 (America/Chicago)
**Repo/worktree:** `alphaguard-wt-option-b` @ `1f53808`
**Freeze:** `001856a6` (Option B features). Go remains **UNCLAIMED**.

## Results
- Observed nested val AUPRC: **0.413021**
- Learning-curve val means by frac: [0.239, 0.2868, 0.3066, 0.3551]
- S2: **VARIANCE-DOMINATED** (gap@100%=0.1566 > seed_spread=0.0429; means non-decreasing → may proceed subject to S3/G4)
- Permutations: n=200, C=1, **p=0.0100**
- S3: **SIGNIFICANT**

## G4
Locked: if p≥0.05 do **not** E2.
**Verdict: E2 ALLOWED** (p=0.0100 < 0.05).

## Next
Await Tom Gate 0 for E2 download/run (large FinBERT job). Do not start E2 until Tom locks start. M2 Pro opts: `--workers 1`, one heavy job, leave ~3–4 GB headroom.
