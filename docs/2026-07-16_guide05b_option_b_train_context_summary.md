# Context: Guide 05b — Option B XGBoost train + option_b bundle

**Date:** 2026-07-16  
**Repos:** `alphaguard`  
**Status:** Draft (Gather) — **Ready for Write-dev-guide**  
**Mode last used:** hub  
**Prioritize SSOT:** `second_brain/docs/2026-07-16_prioritize_next_work_pass70_fan_in.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md` (incl. FinBERT soft pin + FB→META defer)  
**Upstream:** Guide 05a Review-shippable — `docs/TRAINING_DATA.md`, `docs/dev_guides/2026-07-16_dev_guide_05a_option_b_dataset_builder.md`  
**Role lens:** ML engineer (+ backend for gate load / fail-closed)

## Problem

Guide 05a produces `data/derived/training_events.parquet` (~500 rows, FinBERT + as-of features + forward-downside labels). Agent 2 still loads a **`bundle_kind=fixture`** stub from `scripts/build_fixture_bundle.py`. Interviewers will correctly reject “Option B gate” claims until an **`option_b`** bundle exists with train/test metrics, train-only threshold fit, and fail-closed load rules (ARCHITECTURE §7.4–§7.6, AG2).

## Acceptance criteria

- [ ] CLI/script trains XGBoost **downside-risk scorer** on regenerable parquet (Guide 05a path)  
- [ ] Time-ordered **80/20** split by `published_at` (**no shuffle**); thresholds fit on **train only**  
- [ ] `score_kind=proba_high_risk`; `score_threshold` = train-F1 max (ARCHITECTURE §7.4)  
- [ ] Writes model bundle + `manifest.json` with `bundle_kind=option_b` and required §7.6 fields  
- [ ] Gate can load Option B bundle; fixture bundle remains for smoke; no silent claim that fixture = Option B  
- [ ] Docs honesty: VISION Option B row / ARCHITECTURE `ml/train` / README show train landed + metrics; still not “v1 complete” without eval judgment  
- [ ] Default smoke still FinBERT-free / does not retrain  
- [ ] Explicit: 5-ticker parquet coverage accepted for first train (MSFT/META/SPY absent from preferred CSV; FB→META deferred)

## In scope

- Train path under `src/alphaguard/ml/` (+ thin `scripts/` CLI)  
- Threshold fitting + metrics logging (train/test)  
- Option B bundle dir under `data/derived/` (gitignored) or documented path  
- Fail-closed gate load for `bundle_kind`  
- Same-delivery docs honesty  

## Out of scope

- Rebuilding Guide 05a dataset builder  
- FB→META alias (deferred; revisit only with soft pin + price-as-META)  
- Live RSS; Option C (train on Agent 1 outputs); brokerage; Lowd Capital  
- Neural calibrator; confidence-weighted thresholds  
- Claiming v1 / interview “model proven” from one small train  

## Prior art (paths only)

- `docs/ARCHITECTURE.md` §6.3, §7.4–§7.6, §11, AG1–AG3  
- `docs/VISION.md` Option B row / MV checklist  
- `docs/TRAINING_DATA.md` (parquet regenerate + universe honesty)  
- `docs/2026-07-15_guide05_option_b_u4_dataset_context_summary.md` (05a; train was out of scope)  
- `scripts/build_fixture_bundle.py` (pattern for train-F1 threshold + manifest — **fixture only**)  
- `src/alphaguard/contracts/manifest.py`, `contracts/decisions.py` (`FEATURE_NAMES`)  
- `src/alphaguard/ml/gate.py` (load / fail-closed)  
- `AGENTS.md`  

## Risks and blast radius

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| Train/serve skew (feature order, dtypes) | Silent bad gates | Manifest `feature_names` must match `FEATURE_NAMES`; fail closed |
| Threshold fit on full data | Inflated metrics / AG2 violation | Split first; fit train only; freeze into manifest |
| Claiming Option B from fixture | Interview honesty fail | `bundle_kind` gate; docs language |
| Overfitting tiny n≈500 | Weak generalization | Honest metrics; no “alpha” claims; time split |
| Overwriting fixture default smoke | Break Guides 01–04 | Separate bundle path; smoke keeps fixture unless explicit env |
| Scope into FB alias mid-train | Join bugs / wrong Yahoo `FB` ETF | Soft pin deferred; document only |

## Edge cases

- Missing parquet → fail closed with regenerate command  
- Class imbalance / all-negative train F1 path → document threshold fallback (e.g. if F1 undefined)  
- Feature NaNs → reject rows or fail closed (prefer fail closed if any NaN in FEATURE_NAMES)  
- `bundle_kind=option_b` requested but fixture path loaded → fail closed  
- Re-train idempotency → overwrite derived bundle dir atomically or versioned `bundle_id`  
- Vol veto: default **off** unless soft-pinned on (ARCHITECTURE allows optional)  

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking? |
|---------|----------------|-----------|
| Exact CLI name / bundle output path | Soft pin in Write-dev-guide | No for Gather |
| XGBoost hyperparams (depth, eta, rounds) | Soft pin small defaults mirroring fixture unless evidence says otherwise | No — pin in guide |
| Enable vol veto in first Option B bundle? | Soft pin: **off** (match fixture default; policy can enable later) | No — recommend off |
| Default smoke switches to Option B? | Soft pin: **no** — fixture remains default smoke | No — recommend no |
| Metrics to print/store | Soft pin: train/test precision/recall/F1 + confusion counts + threshold | No |

## Recommended approach

1. **Do not** rebuild multi-repo architecture context or a second comprehensive Option B dataset context — 05a + ARCHITECTURE are SSOT for data.  
2. Write-dev-guide 05b: thin train CLI, reuse fixture threshold pattern, write `option_b` bundle, wire gate load path, docs honesty.  
3. Implement only after Ready-check.  
4. FB→META stays deferred until optional pre-Implement soft pin.

## Open decisions (human) — locked this pass unless reopened

Tom agreed 2026-07-16 (Prioritize pass 70 recommendations):

| Decision | Locked choice |
|----------|---------------|
| Authorize Guide 05b path | **Yes** — Gather → Write-dev-guide next |
| FB→META alias | **Deferred** |
| First train ticker coverage | **Accept 5-ticker** parquet (AAPL/AMZN/GOOGL/NVDA/QQQ) with honesty docs |
| Mechanic freeze / Vehicle S9 / AI KB deeper eval | **Parked** for now |

### Soft pins to set in Write-dev-guide (not blocking Gather)

- **Plain title:** Should the first Option B bundle enable volatility veto?  
  - Recommendation: **No** (`vol_veto_enabled=false`) — keep policy simple; fixture already demonstrates veto path in eval harness.  
  - Tradeoffs: Less policy surface; can enable in a later guide with train-fitted percentile.  

- **Plain title:** Should default smoke load the Option B bundle after train?  
  - Recommendation: **No** — keep fixture as default smoke; document how to point gate at Option B for demos.  
  - Tradeoffs: Demo path needs an env/flag; avoids breaking CI/smoke on missing derived bundle.  

## Evidence opened this pass

- ARCHITECTURE §6.3 / §7.4–§7.6 / §11  
- `scripts/build_fixture_bundle.py` threshold + manifest pattern  
- `FEATURE_NAMES` in `contracts/decisions.py`  
- TRAINING_DATA live e2e + Yahoo META/FB evidence (pass 70)  
- Prioritize pass 70; Review pass 69  
- Canvas `multi-repo-architecture-review.canvas.tsx` — **stale** (July 12 “no repo ready to implement”); not SSOT for Guide 05 delivery  

## Honest readiness

- Ready for Write-dev-guide? **Yes.**  
- Why not rebuild comprehensive context: Guide 05a context + ARCHITECTURE already lock labels, split order, score kind, manifest schema, and feature list. This file only adds **train-specific** scope, risks, and soft-pin recommendations.  
- Context quality: **good enough** for an executable Guide 05b. Refine-context optional if Write-dev-guide surfaces forks.  
