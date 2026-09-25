<!-- Author: Claude Opus (claude -p --model opus) on Mac 2026-09-25 ~2:00 PM CT; executor: Job Hunt / Grok Bot. PLAN ONLY. -->

# AlphaGuard Option B: Features and a New Freeze

**File:** `docs/plans/2026-09-25_jh63_option_b_features_freeze_plan.md`
**Status:** PLAN ONLY · NOT YET CODED · 2026-09-25 CT
**Current freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` (n=8907)
**Model Quality Go:** UNCLAIMED. The Option A clean nested Fail stands (seeds 42/7/123, `runs/optionA_2026-09-25/purge_align/summary.md`).

## Goal
The model is starved for signal. Option A showed that the earlier passing score came from leakage. With the leak removed, five features are not enough to clear the floors. Option B gives the model four more market signals that we can compute from price history we already fetch. It rebuilds the dataset as a new, versioned freeze and re-runs the same honest tests. We don't add rows, change the label or tune harder. Only the inputs change.

## Non-goals
- No denser grid, no Matrix C expansion, no new hyperparameter search.
- No label change (`fwd_return_5d < -0.03` stays). No relabel. No headline dedupe.
- No floor change (F1≥0.30, P≥0.25, AUPRC≥0.18) without Tom.
- No sample expansion. n=8907 is the deduped inventory ceiling.
- No new models (FinBERT stays as is). No volume fetcher.
- No Go claim, even if every floor clears. No public voice.
- No OMP rework. `thread_limits.py` and the Darwin `workers=1` default stay as they are.

## Feature choice (pre-registered; judgment locked)
There are 4 new features, for 9 total. Every one comes from closes inside the **existing `prior20 → feature_as_of` window**. This keeps the lookback the same, so no rows drop and n stays 8907. A 60-day window would drop early rows and silently change n, so it is rejected.

| Feature | Definition (as-of `feature_as_of`) | Why |
|---|---|---|
| `rs_20d` | `return_20d_prior − spy_return_20d` | This is ticker-specific weakness separated from the market. Trees can't easily learn a difference of two inputs, so we give it explicitly. It uses the 20-day window because `rs_5d` would be a linear combination of two existing columns. |
| `drawdown_20d` | `close(as_of) / max(close[prior20..as_of]) − 1` | This measures distance from the recent high. It is a path feature that the endpoint returns can't express. |
| `volatility_5d` | annualized std of the 5 daily returns in `[prior5..as_of]` | A short-term vol spike compared with the 20-day regime is a classic precursor to a drawdown. |
| `spy_volatility_20d` | `_vol_20d` on SPY closes | This is the market-stress regime. Option A found positives clustered on market-wide selloff days. |

These are rejected: `return_1d/10d_prior` (redundant with the 5d/20d returns), SMA distance (collinear with `drawdown_20d`), volume (needs a new fetcher, out of cheap scope) and 60-day windows (they change n).

**Anti-shopping rule:** this set is fixed before any run. If the acceptance runs FAIL, Grok does **not** swap features and re-run. It stops and goes to the decision gate.

## Work packages (executor: Grok 4.7 local)
Outputs go to `runs/optionB_2026-09-25/<wp>/summary.md`. Each summary records the freeze hash and the script path.

### WP-B0: Preconditions
- [ ] The branch contains the purge-aligned nested split and `thread_limits.py` (see Handoff gate 0).
- [ ] Back up `data/derived/training_events.parquet` to `data/derived/training_events_jh633_534a341a.parquet`, following the pattern of `training_events_jh631_a8bdd0fb.parquet`. Verify the backup's `dataset_hash` equals `534a341a…` before anything overwrites the original.

### WP-B1: Feature code and tests
- [ ] `src/alphaguard/ml/dataset_asof.py`:
  - Generalize `_vol_20d` to `_vol_window(series, as_of, sessions, n)` and keep `_vol_20d` as a thin wrapper so existing behavior is byte-identical.
  - Add `_drawdown_window(...)`.
  - In `compute_features_and_label`, compute `spy_return_20d` (internal, not a model feature), `rs_20d`, `drawdown_20d`, `volatility_5d` and `spy_volatility_20d`.
  - Add all four to the `None` fail-closed tuple and to the returned dict.
  - Leave the SPY fetch range (`prior20 → feature_as_of`) unchanged.
- [ ] `src/alphaguard/contracts/decisions.py`: append the 4 names to `FEATURE_NAMES` after the existing 5 and keep the original order.
- [ ] Grep every consumer of `FEATURE_NAMES` and of the feature dict: `train_hpo.py`, `study_walkforward.py`, `train_option_b.py`, `scripts/build_training_events.py`, any serving/inference path and the fixtures. Update or fail closed. Old model bundles must refuse to load with a 9-column input and must not silently mis-map features.
- [ ] Tests:
  - Hand-computed values for each new feature on a synthetic close series.
  - No-lookahead: perturbing any close after `feature_as_of` leaves all features unchanged.
  - `None` when the window is incomplete.
  - The existing 5 features stay byte-identical to the old outputs.
- [ ] Update `docs/TRAINING_DATA.md` with the feature table above.
- [ ] Run the full `pytest`. It must be green with the output attached.

### WP-B2: Rebuild the freeze
- [ ] Run `scripts/build_training_events.py` with FinBERT **on**. `--skip-finbert` is forbidden. Use `--skip-download` if the raw data is present, and use the cached close fetcher.
- [ ] Assert **n == 8907** and that label prevalence matches the old freeze exactly. The label code didn't change, so any drift is a bug. **STOP** on mismatch.
- [ ] Assert the `finbert_sentiment` column is identical to the backup, joined on the row key.
- [ ] Compute `train_option_b.dataset_hash`. Assert it is **≠ `534a341a…`**. Record the new hash as `<NEW8>`.
- [ ] Record a 0 NaN count over the 9 features.

### WP-B3: Study configs
- [ ] Clone `configs/studies/jh63_go_gate_nested_purge_534a.yaml` to `jh63_go_gate_nested_purge_<NEW8>.yaml`, with the new hash and the same grid, floors and seeds.
- [ ] Create `jh63_wf_expanding4_<NEW8>.yaml`, mirroring the Phase B purge-on expanding4 config with the new hash.
- [ ] Leave the `534a` configs untouched. They are historical record.

### WP-B4: Acceptance runs (Mac: `--workers 1` unless Tom overrides)
- [ ] **(a) Nested Go, purge-aligned** (`walk_forward=off` now purges): seeds 42/7/123 with the same floors. Report F1, P, AUPRC, n_train and n_test per seed.
- [ ] **(b) expanding4 WF, purge-on:** per-fold metrics for comparison with the Phase B purge-on re-run on `534a`.
- [ ] Report XGB gain importance for the 9 features for each seed.
- [ ] Write a side-by-side table comparing `534a` clean nested with `<NEW8>` clean nested. Every number needs an artifact path.
- [ ] Verdict per seed is PASS or FAIL against the floors. A seed only passes if all three floors clear.

### WP-B5: Summary
- [ ] Write `runs/optionB_2026-09-25/summary.md`. Label every claim Verified, Unverified or Unknown. Go is UNCLAIMED regardless of outcome. The `534a` Fail results remain Fail in the historical record.
- [ ] Add an `EXPERIMENTS.md` entry pointing to the summary.

## NOTE: cross-split duplicate headlines (not a WP)
Option A found **14** headlines that appear on both sides of a split. FinBERT gives duplicates the same score, so they can leak a small amount of signal. **This plan does not authorize dedupe or relabel.** WP-B4 only re-counts them on the new splits and reports the number in the summary. Whether to remove them is Tom's call after B.

## Decision gates (Tom)
0. **Before Grok starts:** the Option A branch changes need to be committed, or otherwise made available on a clean branch. That covers purge-align, `thread_limits`, `conftest` and the study changes. Grok must not work in the dirty `analysis/option-a-2026-09-25` checkout.
1. **WP-B2 n or prevalence mismatch:** stop. Tom reviews before anything proceeds.
2. **After WP-B4:**
   - **All seeds PASS:** Go is still UNCLAIMED. Tom decides the next confirmation step, such as a locked-test hold-out review. There is no auto-claim.
   - **Mixed or FAIL:** the Fail stands. Tom chooses between a floor review, parking the work, or authorizing a *new* pre-registered feature slice (for example volume). Grok does not iterate on its own.

## Done criteria (evidence before done)
- The backup parquet exists and its hash is verified as `534a341a…`.
- The new hash is ≠ `534a341a…`, n = 8907, prevalence is unchanged and FinBERT is identical.
- `pytest` is green with the output captured.
- The WP-B4 artifacts exist for all 3 seeds and all WF folds, and every quoted metric has a path.
- `git status` shows only Option B files plus the new configs and the backup. Everything stays uncommitted.

## Handoff
- **Next:** after gate 0, Grok 4.7 (local `agent`) runs WP-B0 through WP-B5 in order on a fresh branch or worktree, e.g. `analysis/option-b-2026-09-25`.
- Escalate to Opus if n drifts, a feature consumer is ambiguous (for example the serving path), or the results don't fit the gate cases.
- **Leave everything uncommitted until Tom says so.**
