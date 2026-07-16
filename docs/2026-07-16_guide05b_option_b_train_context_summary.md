# Context: Guide 05b — Option B XGBoost train + option_b bundle

**Date:** 2026-07-16  
**Repo:** `alphaguard`  
**Status:** **Refined** (pass 72) — Write-dev-guide **authored** pass 73 → `docs/dev_guides/2026-07-16_dev_guide_05b_option_b_xgboost_train.md`  
**Next:** Refine-dev-guide or Ready-check (human)  
**Mode last used:** hub  
**Prioritize SSOT:** `second_brain/docs/2026-07-16_prioritize_next_work_pass70_fan_in.md`  
**Gather fan-in:** `second_brain/docs/2026-07-16_gather_context_guide05b_pass71_fan_in.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`  
**Upstream:** Guide 05a Review-shippable — `docs/TRAINING_DATA.md`, `docs/dev_guides/2026-07-16_dev_guide_05a_option_b_dataset_builder.md`  
**Role lens:** ML engineer (+ backend for gate load / fail-closed)

## Problem

Guide 05a produces regenerable `data/derived/training_events.parquet` (~500 rows; live e2e verified 2026-07-16). Agent 2 still loads **`bundle_kind=fixture`** (`scripts/build_fixture_bundle.py`). Interviewers correctly reject “Option B gate” claims until an **`option_b`** bundle exists with time-split train/test metrics, **train-only** threshold fit, and fail-closed load (ARCHITECTURE §7.4–§7.6, AG2).

**Live parquet facts (do not invent):** tickers `AAPL, AMZN, GOOGL, NVDA, QQQ`; `label_high_risk` rate ≈ **0.164**; FinBERT = `ProsusAI/finbert`; MSFT/META/SPY absent from preferred CSV; FB→META deferred.

## Acceptance criteria

- [ ] Thin CLI trains XGBoost downside-risk scorer on Guide 05a parquet  
- [ ] Time-ordered **80/20** by `published_at` (**no shuffle**); fit thresholds on **train only**  
- [ ] `score_kind=proba_high_risk`; `score_threshold` = train-F1 max (§7.4)  
- [ ] Bundle dir + `manifest.json` with `bundle_kind=option_b` and all §7.6 required fields  
- [ ] Gate loads Option B via existing `MODEL_BUNDLE_DIR` (or documented env); **default smoke stays fixture**  
- [ ] Fail-closed honesty: docs + load path never present fixture metrics as Option B; guide specifies any new `bundle_kind` guard if needed  
- [ ] Same-delivery VISION / ARCHITECTURE / README / TRAINING_DATA honesty + printed train/test metrics  
- [ ] Unit tests: split order, train-only threshold, NaN fail-closed, manifest feature_names match `FEATURE_NAMES`  
- [ ] 5-ticker coverage accepted with documented honesty (no invented MSFT/META/SPY)

## In scope

- `src/alphaguard/ml/` train helpers + thin `scripts/train_option_b_gate.py` (name soft-pinned in guide)  
- Threshold fitting + metrics (train/test precision, recall, F1, confusion counts, threshold)  
- Output: `data/derived/model_bundle_option_b/` (gitignored under `data/derived/`)  
- Docs honesty; optional explicit env to point smoke/demo at Option B (**not** default)

## Out of scope

- Rebuilding 05a builder; FB→META alias; live RSS; Option C; brokerage; Lowd Capital  
- Neural calibrator; confidence-weighted thresholds  
- Switching default CI/smoke to Option B  
- Claiming v1 complete / “alpha proven” from n≈500  

## Prior art (paths only)

- `docs/ARCHITECTURE.md` §6.3, §7.4–§7.6, §11, AG1–AG3  
- `docs/VISION.md` Option B / Minimum Viable  
- `docs/TRAINING_DATA.md`  
- `docs/2026-07-15_guide05_option_b_u4_dataset_context_summary.md`  
- `scripts/build_fixture_bundle.py` (train-F1 + manifest pattern — **fixture only**)  
- `src/alphaguard/contracts/manifest.py`, `contracts/decisions.py` (`FEATURE_NAMES`)  
- `src/alphaguard/ml/gate.py` (`DownsideRiskGate`, `MODEL_BUNDLE_DIR` in error text)  
- `AGENTS.md`  

## Risks and blast radius

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| Train/serve skew | Bad gates in demos | Manifest `feature_names` == `FEATURE_NAMES`; fail closed |
| Threshold fit on all rows | AG2 violation / inflated test F1 | Split first; fit train only; freeze |
| Fixture quoted as Option B | Interview fail | `bundle_kind` in docs + metrics; keep smoke on fixture |
| Tiny n / imbalance (~16% positive) | Unstable F1 / threshold | Honest metrics; document; F1-undefined fallback soft pin |
| Overwriting fixture path | Break Guides 01–04 | Separate derived bundle dir only |
| Gate lacks mode×`bundle_kind` assert today | Honesty hole if docs claim Option B while fixture loaded | Guide: either env `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` for Option B demos **or** document that path selection is operator-owned; prefer small fail-closed check when env set |

## Edge cases

- Missing parquet → fail closed + regenerate command from TRAINING_DATA  
- Train F1 undefined (no positives/negatives) → fail closed or documented fallback threshold (soft pin: **fail closed** with clear error)  
- NaNs in `FEATURE_NAMES` columns → fail closed  
- Re-train → atomic replace of derived bundle dir (write tmp → replace)  
- `vol_veto_enabled=false` for first Option B bundle (soft pin)  
- Yahoo/FB alias **not** in this guide  

## Unknowns → soft pins for Write-dev-guide

| Soft pin | Recommended lock |
|----------|------------------|
| CLI | `scripts/train_option_b_gate.py` |
| Bundle out | `data/derived/model_bundle_option_b/` |
| Parquet in | `data/derived/training_events.parquet` (require exists; `--parquet` override OK) |
| XGBoost params | Mirror fixture starter: `max_depth=3`, `eta=0.1`, `num_boost_round=50`, `seed=42`, `objective=binary:logistic` (small; guide may note tune later) |
| Vol veto | **`vol_veto_enabled=false`** |
| Default smoke | **Fixture** remains default; Option B via `MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b` |
| Metrics | Train+test: precision, recall, F1, TP/FP/TN/FN, `score_threshold` |
| F1 undefined | **Fail closed** |
| `bundle_id` | `option-b-downside-v1` |
| `model_version` | `0.1.0-option-b` |

## Recommended approach

1. Write-dev-guide with ordered checklist + DoD from soft pins above.  
2. Ready-check → Implement train only.  
3. Review → metrics honesty.  
4. FB→META still deferred.

## Open decisions (human)

### Locked (Tom 2026-07-16)

| Decision | Lock |
|----------|------|
| Guide 05b path | Authorized |
| FB→META | Deferred |
| 5-ticker first train | Accepted |
| Mechanic freeze / Vehicle S9 / AI KB deeper eval | Parked |

### Soft pins (recommend lock at Write-dev-guide; not blocking Refine)

1. **Vol veto off** for first Option B bundle — yes.  
2. **Smoke stays fixture** — yes.  
3. **XGBoost starter hyperparams** as table above — yes (simple, reproducible).  
4. **Canvas:** replace stale architecture-review canvas with current portfolio progress board (this hub pass) — yes.

## Evidence opened this refine pass

- Re-read ARCHITECTURE §7.4–§7.6; `gate.py` (no `bundle_kind`×mode assert yet)  
- `build_fixture_bundle.py` threshold loop  
- TRAINING_DATA e2e ticker/label facts  
- VISION Minimum Viable checkboxes (05b still open)  
- Portfolio VISION/status for Mechanic, AI KB, Vehicle (progress report)

## Honest readiness

| Score | Value |
|-------|--------|
| **Write-dev-guide readiness** | **8.7 / 10** |
| Ready? | **Yes** |

**Why not 10:** (1) Exact hyperparams are recommended not yet human-echoed as soft pins in a guide file; (2) whether to add env-gated `bundle_kind` assert is a small design fork for the guide; (3) Implement will still discover edge cases on real class imbalance. None block writing an executable guide.

**Do we need more context first?** **No.** Next stage: **Write-dev-guide**.
