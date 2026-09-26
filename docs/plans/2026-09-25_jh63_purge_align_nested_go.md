<!-- Author: Claude Opus (claude -p --model opus) on Mac 2026-09-25 ~1:45 PM CT; executor: Job Hunt / Grok Bot. PLAN ONLY. -->

# AlphaGuard JH63: Purge-Align the Nested Go-Gate

**Status:** PLAN ONLY · NOT YET CODED · 2026-09-25 CT
**Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` (unchanged; no new parquet)
**Model Quality Go:** UNCLAIMED. The Phase C Go-gate FAIL stands.
**Decision (Tom, locked):** Option A verdict (a). Label/leakage is binding. This slice fixes the nested split only. No relabel.

## Goal
Stop the nested Go-gate from training on rows whose label windows reach into the locked test. Technical cut: `walk_forward=off` uses the same locked-test trading-day purge that `expanding4` already uses.

Evidence (Verified): `docs/plans/optionA_verdict_2026-09-25.md`, `runs/optionA_2026-09-25/rollup.json`, `runs/optionA_2026-09-25/wp_a1/overlaps.json`. Nested off has 92 same-ticker overlaps (GOOGL, META, NVDA, QQQ). Purge-on WF has 0. Counterfactual train_end 7125→7029 (96 rows dropped). n_dev = 7125.

## Exact code touchpoints

### Change
- `src/alphaguard/ml/study_walkforward.py::split_for_walk_forward` (line ~158)
  - Today: `if walk_forward != "expanding4": return time_ordered_split(...)` (line 166). That early return is the bug. The nested path never reaches the purge.
  - Fix: delete that early return. The rest of the function already does the right thing for both modes: `_session_indices(df)` → `boundary = int(n_rows * train_frac)` → `prefix_end_before_session(label_end_idx, candidate_end=boundary, next_session=min(feature_idx[boundary:]))` → `train = df.iloc[:train_end]`, `test = df.iloc[boundary:]`.
  - Keep every fallback to `time_ordered_split`: no session indices, boundary out of range, or `train_end == boundary`.
  - Optional guard: raise `ValueError` if `walk_forward not in ("off", "expanding4")`. Match the message in `study_phaseb.py:47`.
  - Update the docstring: "With session dates, both `off` and `expanding4` purge the locked-test gap. Without them, historical 80/20 cut with no gap."
- `tests/test_phase_c_audit.py::test_locked_test_split_drops_straddling_train_rows` (line 163)
  - Keep the existing asserts. `plain` (session columns dropped, `"off"`) stays at `boundary`. `purged` (`"expanding4"`) stays at `boundary - 6`.
  - Add: `nested = split_for_walk_forward(df, 0.8, "off")` on the frame WITH session columns. Assert `len(nested.y_train) == boundary - 6` and `len(nested.y_test) == n - boundary`.

### Do not touch
- `src/alphaguard/ml/train_option_b.py::time_ordered_split`. Frames without session dates must keep their row counts.
- `src/alphaguard/ml/study_executor.py::execute_run`. It already calls `split_for_walk_forward` (line 138). The inner val cut via `train_val_sizes` (line 163) stays unpurged. That is out of scope for this change.
- `evaluate_expanding4`, `expanding4_folds` and `apply_trading_day_embargo`. WF folds are already purged. Do not retune.
- `src/alphaguard/ml/study_cli.py`. `--walk-forward` stays default `off`.
- PROMOTION_POLICY, claim docs, `docs/EXPERIMENTS.md`, and the old study `configs/studies/jh63_go_gate_phase_c_534a.yaml`.

## Acceptance checks
Run all of these after the code change. Write the outputs to `runs/optionA_2026-09-25/purge_align/`.

1. **Unit:** `uv run pytest tests/test_phase_c_audit.py -q` passes, including the new `off`-with-sessions case.
2. **Full suite:** `uv run pytest -q` passes. If another test's frame carries `feature_as_of` and its train count shifts, stop and escalate. Do not loosen the assertion.
3. **Real-data one-shot** (`scripts/option_a/nested_purge_align_check.py`, untracked). This reuses the WP-A1 counterfactual; it adds no new metric:
   - Load `data/derived/training_events.parquet` with `load_training_frame`. Assert `dataset_hash(x, y) == FREEZE_HASH`.
   - Call `split_for_walk_forward(df, 0.8, "off")`. Assert `len(y_train) == 7029` and `len(y_test) == n - 7125`. That puts the test start at 7125, so n_dev is unchanged.
   - Get `feat, lab = frame_session_indices(df)`. Import `same_ticker_overlaps` from `scripts/option_a/wp_a1_residual_leakage.py`. Call `same_ticker_overlaps(tickers, feat, lab, published_at, train_end=7029, test_start=7125, test_end=n)`. Assert `overlap_train_rows == 0`.
   - Assert `prefix_end_before_session(lab, candidate_end=7125, next_session=min(feat[7125:])) == 7029`, which must match `nested_path.purge_on_counterfactual.train_end` in `runs/optionA_2026-09-25/wp_a1/overlaps.json` and `wp.a1.nested_purged_train_end` in `runs/optionA_2026-09-25/rollup.json`.
   - Write `check.json` with the freeze hash, script path, the counts above, and `model_quality_go: "UNCLAIMED"`.
4. **Freeze:** every run record in the new study has `dataset_hash_match: true` and hash `534a341a…2cb3`. No new parquet appears under `data/`.
5. **Headlines:** the cross-split count (14) is a NOTE only. It is not a pass/fail for this change. Do not dedupe headlines.
6. **Go:** stays UNCLAIMED even if all three seeds clear F1≥0.30, P≥0.25 and AUPRC≥0.18. The harness may log `promotion_decision`. Report it as Unverified-for-Go until Tom decides.

## Re-run: nested multi-seed Go only
New config `configs/studies/jh63_go_gate_nested_purge_534a.yaml`. Copy `jh63_go_gate_phase_c_534a.yaml` exactly and change only:
- `study_id: jh63_go_gate_nested_purge_534a`
- `description: "Nested Go-gate on freeze 534a341a with locked-test trading-day purge aligned to expanding4 (train_end 7029); matrix C winner hparams; Go UNCLAIMED"`

Everything else stays the same:
- seed 42
- `train_val_fbeta_0.5`, beta 1.0, isotonic calibration
- max_depth 2, eta 0.1, 40 rounds, scale_pos_weight 2
- `nested_time_aware_v1`, train_frac 0.8, val_frac 0.2
- promotion enabled, shortlist 3, extra_seeds 7 and 123
- floors 0.30/0.25/0.18, sort_by test_f1

Command (walk-forward stays at default `off`; do NOT pass `--walk-forward expanding4`):
```
uv run python scripts/run_study.py --study configs/studies/jh63_go_gate_nested_purge_534a.yaml --workers 2
```
Artifacts: `artifacts/runs/studies/jh63_go_gate_nested_purge_534a/`. The Phase C FAIL study at `artifacts/runs/studies/jh63_go_gate_phase_c_534a/` must be byte-for-byte untouched.

Report per seed (42/7/123): test F1, P, AUPRC, n_train (expect 7029), n_test, and floors pass/fail. Compare against the old Phase C FAIL numbers. Label every number Verified with its artifact path.

## Out of scope
- Option B, denser grids, any new hparam search.
- Relabel or any change to `fwd_return_5d < -0.03`.
- Headline dedupe.
- WP-A4. It is BLOCKED (no saved predictions). Do not re-run the grid to regenerate them.
- Claiming Go, editing PROMOTION_POLICY or claim docs.
- Committing, pushing or opening a PR without Tom.
- Overwriting or re-running `jh63_go_gate_phase_c_534a`.
- Changing `time_ordered_split`, purging the inner val cut, or changing WF fold logic.

## WP checklist (Grok 4.7 local, in order)
1. **Read.** Read `split_for_walk_forward`, `execute_run` lines 120–170 and the test at `tests/test_phase_c_audit.py:163`. **Done:** confirm the early return at `study_walkforward.py:166` is the only path that skips the purge. If the code disagrees with this plan, stop and escalate to Opus.
2. **Test first.** Add the `off`-with-sessions assert. **Done:** it fails on the current code (train len == boundary, not boundary − 6).
3. **Fix.** Remove the early return, update the docstring, add the optional mode guard. **Done:** `uv run pytest tests/test_phase_c_audit.py -q` is green.
4. **Full suite.** **Done:** `uv run pytest -q` is green, with no assertion loosened.
5. **One-shot check.** Write and run `scripts/option_a/nested_purge_align_check.py`. **Done:** `runs/optionA_2026-09-25/purge_align/check.json` shows train 7029, test start 7125, same-ticker overlaps 0, and freeze hash match.
6. **Config.** Create `configs/studies/jh63_go_gate_nested_purge_534a.yaml`. **Done:** a diff against the Phase C yaml shows only `study_id` and `description` changed.
7. **Re-run.** Run the command above. **Done:** the artifact dir exists, all three seeds have records with `dataset_hash_match: true` and n_train 7029, and the old study dir's mtime is unchanged.
8. **Summary.** Write `runs/optionA_2026-09-25/purge_align/summary.md` with the per-seed table, the floors, the old-vs-new delta, the 14-headline NOTE, and "Model Quality Go: UNCLAIMED". **Done:** every number cites an artifact path.
9. **Stop.** Hand off to Job Hunt for Tom.

Leave git uncommitted. Work on the current tree: HEAD is main `2277165`, branch `analysis/option-a-2026-09-25`, with untracked analysis files (`configs/studies/jh63_matrix_c_8907.yaml`, `docs/plans/`, `runs/`, `scripts/option_a/`). Do not commit them.
