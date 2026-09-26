# WP-A4: Error taxonomy — BLOCKED

- **Verdict:** BLOCKED
- **Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
- **Script:** `scripts/option_a/run_option_a.py (executor inline 2026-09-25)`

## Blocker

Saved row-level predictions are missing for nested seeds 42/7/123 and purge-on WF expanding4. Bundles contain model.json+manifest+README only; run.json has aggregate metrics/confusion but not per-row scores. Per plan WP-A4 blocker: stop and report; do not re-run the grid to regenerate them.

## What exists

- Nested Go-gate bundles under `artifacts/runs/studies/jh63_go_gate_phase_c_534a/bundles/`: model.json, manifest.json, README.md only.
- Nested run.json: aggregate metrics + confusion counts only.
- Purge-on WF `runs/phaseb_phasec_2026-09-25/seed*/`: no row-level predictions.

## Not done (by design)

- No grid re-run
- No scoring pass claimed as saved predictions
- FN/FP taxonomy deferred until predictions are authorized/available

## Artifacts

- `runs/optionA_2026-09-25/wp_a4/blocker.json`
- `runs/optionA_2026-09-25/wp_a4/summary.md`
