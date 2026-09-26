<!-- Author: Claude Opus (claude -p --model opus) on Mac 2026-09-25 ~1:20 PM CT; executor: Job Hunt / Grok Bot. PLAN ONLY. -->

# AlphaGuard Option A: Label, Prevalence and Residual-Leakage Diagnosis

**Status:** PLAN ONLY · NOT YET CODED · 2026-09-25 CT
**Freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` (main, after PR #18)
**Model Quality Go:** UNCLAIMED. The Fail stands.

## Goal
Find out whether the label definition, prevalence, hard cases or residual leakage explain why the floors fail. Option A only diagnoses. It produces evidence and a verdict, not a better model.

## Non-goals
- No denser XGB grid and no new hyperparameter search.
- No feature rebuild, no new freeze, no Option B work. Option B stays queued until A has a verdict.
- No Go claim and no re-labeling of any Fail.
- No change to the label (`fwd_return_5d < -0.03`) during A. A may only *recommend* a change.

## What Phase C already proved vs what A still needs

| Area | Phase C proved (Verified, `runs/phasec_2026-09-25/audit/`) | Option A still needs |
|---|---|---|
| Label correctness | C1: 0 label mismatches | Whether the label is *learnable* (near-threshold mass, clusters) |
| As-of / construction | C3: 0 as-of violations; 0 construction dups | Leakage *after* construction: same-ticker label windows spanning the train/test boundary |
| Purge | Row-embargo left 229 overlap rows; trading-day purge → 0 | Why purge-on WF made F1/P **worse** on all seeds; nested path runs with `walk_forward=off` (no purge) |
| Prevalence | Full 0.169; locked_test 0.1308 | Whether AUPRC ≥ 0.18 is realistic against the null baseline |
| Regime | fold_0 artifact (NVDA); folds 1–3 + locked_test regime | How much fold_0 distorts training |
| Rules | C4 misaligned (2/4) | Out of scope for A unless WP-A4 links rule misalignment to errors |

## Work packages (executor: Grok 4.7 local)
Every WP reads existing freeze data and existing FAIL-run artifacts only. Outputs go to `runs/optionA_2026-09-25/<wp>/`, with a `summary.md` and machine-readable JSON/CSV per WP.

### WP-A1: Residual leakage beyond C3
- For each WF fold and the nested path: count train rows whose `[t, t+5 trading days]` label window overlaps any test row for the **same ticker**, reported separately with purge on and purge off.
- Diff the nested path (`jh63_go_gate_phase_c_534a`, `walk_forward=off`) against WF expanding4. Report whether the nested splits hold any overlap the purge would have removed.
- If headline/FinBERT features exist: count exact or near-duplicate headlines (normalized text hash) that appear on both sides of a split.
- **Pass:** 0 same-ticker label-window overlaps on the purge-on WF path, and nested-path overlap is quantified (count plus the affected tickers and dates).
- **Fail/flag:** any overlap on purge-on WF, or cross-split headline repeats above 0. Tabulate them without fixing anything.
- **Question to answer:** did pre-purge Phase B scores benefit from leakage? (Purge-on scores being worse is consistent with that, but does not prove it.)

### WP-A2: Label epidemiology and hard cases
- Histogram `fwd_return_5d` near the threshold. Report the share of positives and negatives inside ±0.5% and ±1% of −0.03, per fold and for locked_test.
- Same-day clusters: the distribution of positives per date across tickers, and the share of positives on dates with ≥50% of tickers positive (market-wide selloffs).
- fold_0: per-ticker positive counts. Quantify the NVDA contribution to the train positives each fold inherits.
- **Pass:** the tables exist and every number traces to a script and the freeze hash.
- **Signal:** a large near-threshold mass or cluster share means the label is noisy or market-driven, not ticker-specific. Record this; do not act on it.

### WP-A3: Prevalence vs floor feasibility
- Compute the null baselines per fold and for locked_test: random-classifier AUPRC ≈ prevalence (locked_test 0.1308), constant-predictor F1, and a prior-only (per-ticker base-rate) baseline.
- Compute the lift over null required to reach AUPRC ≥ 0.18, and compare it with the lift the existing FAIL runs achieved (read from their artifacts; compute nothing new).
- **Pass:** a written statement, per seed, of whether the floors demand lift beyond what the existing runs show.
- **Flag:** if the floors sit near the prevalence noise band on this sample size, say so explicitly. Bootstrap CIs on the existing predictions are allowed; retraining is not.

### WP-A4: Error taxonomy on existing FAIL runs (diagnostic only)
- Inputs: saved predictions from nested seeds 42/7/123 and purge-on WF expanding4. No retraining.
- Slice FN and FP by near-threshold (WP-A2 bins), cluster day vs idiosyncratic, ticker, fold/regime, and C4 rule-misaligned rows.
- Explain the seed variance: which slices flip between seed 42 (PASS floors) and seeds 7/123 (FAIL).
- **Pass:** an FN/FP taxonomy table plus the top-3 slices by error mass, each tied to WP-A1, A2 or A3 evidence.
- **Blocker:** if saved predictions are missing, stop and report. Do not re-run the grid to regenerate them.

### WP-A5: Verdict
Write `docs/plans/optionA_verdict_2026-09-25.md` with exactly one conclusion:
- **(a) Label/leakage IS binding:** name the specific cause and a proposed label or purge change → Tom decides on a relabel slice before Option B.
- **(b) It is NOT binding:** the label is clean and the floors are feasible → unlock Option B (features plus a new freeze).
- **(c) The floors are infeasible at this prevalence and sample size:** recommend a floor review → park both A and B pending Tom.

Label every claim Verified, Unverified or Unknown. Go stays UNCLAIMED in all three outcomes.

## Decision gates (Tom, only if blocking)
1. **After WP-A5:** choose between relabel, Option B or a floor review. This is the only planned gate.
2. **Ad hoc:** if WP-A1 finds overlap on the purge-on WF path, the Phase B/C Fail artifacts need an errata note. Tom approves the wording.

## Done criteria (evidence before done)
- Every WP output directory has `summary.md` plus its data files, and each records the freeze hash and the script path.
- No new metric is quoted without an artifact path.
- `git status` shows Option A files only. Nothing touches the model config or grid.

## Handoff
- **Next:** Grok 4.7 (local `agent`) implements WP-A1 through WP-A4 in order, then drafts WP-A5 for Opus review.
- Work on a separate branch or worktree off main. Do not share the dirty checkout on `docs/phaseb-phasec-purge-rerun-2026-09-25`.
- **Leave everything uncommitted until Tom says so.**
- Escalate to Opus if a WP result is ambiguous or the verdict criteria don't fit the evidence.
