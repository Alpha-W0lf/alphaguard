# Dev Guide 05b — Option B XGBoost train + `bundle_kind=option_b`

**Date:** 2026-07-16  
**Repo:** `alphaguard`  
**Work item:** Guide 05b — train downside-risk XGBoost on Guide 05a parquet; write Option B model bundle  
**Stage that authored this:** Write-dev-guide (pass 73); Refine-dev-guide (pass 74); **verify Refine (pass 76)**  
**Status:** **Implement complete (pass 77)** — awaiting Review-implementation. Ready-check was **9.0/10**.

**Context SSOT:** `alphaguard/docs/2026-07-16_guide05b_option_b_train_context_summary.md`  
**Upstream dataset:** Guide 05a Review-shippable — `docs/TRAINING_DATA.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`  
**Prerequisite:** Regenerable `data/derived/training_events.parquet`. Guides 01–04 shippable. Fixture gate remains default smoke.

---

## Objective

Train a reproducible **XGBoost binary classifier** that emits `downside_risk_score = P(label_high_risk=1)`, using **nested time-aware hyperparameter selection on train only**, fit **`score_threshold` on train only** (train-F1 max), write `bundle_kind=option_b`, and update docs honesty — **without** claiming v1 Done or switching default smoke off the fixture bundle.

**Success signal:** One CLI produces `data/derived/model_bundle_option_b/` with audited manifest (params, search method, train/test metrics); default `make smoke` still fixture; Option B demo via `MODEL_BUNDLE_DIR` + optional `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b`.

---

## Are hyperparameters (HPO) necessary?

**HPO** = **hyperparameter optimization** (choosing model knobs like tree depth and learning rate — not the learned tree weights themselves).

**Yes — for a senior portfolio gate.** Skipping selection entirely looks like a demo shortcut. Blind Optuna on the full dataset (or on the test fold) looks worse.

**Right-sized practice for n≈500 temporal rows:**

| Do | Do not |
|----|--------|
| Small **grid** on **train only** via `TimeSeriesSplit` | Random K-fold (leaks future → past) |
| Select booster by **mean validation logloss** | Optimize test F1 during search |
| Refit winner on **full train**; fit threshold on train | Tune threshold on test |
| Log search space + winner into manifest | Hide how params were chosen |
| Keep grid tiny (overfit-aware) | Huge Bayesian search / dozens of trials |

**Soft-pinned search space (8 candidates):**

| Dim | Values |
|-----|--------|
| `max_depth` | `{2, 3}` |
| `eta` | `{0.05, 0.1}` |
| `num_boost_round` | `{40, 60}` |

**Fixed for all candidates (regularization / imbalance):**

```text
objective=binary:logistic
eval_metric=logloss
seed=42
min_child_weight=1
subsample=0.8
colsample_bytree=0.8
reg_lambda=1.0
scale_pos_weight = n_neg_train / n_pos_train   # train only; fail closed if n_pos_train==0
```

**Inner CV:** `sklearn.model_selection.TimeSeriesSplit(n_splits=3)` on the **train** partition only.  
**Fold score:** `sklearn.metrics.log_loss(y_true, y_proba)` on each validation fold (probabilities from that fold’s booster).  
**Selection rule:** lowest **mean** validation logloss across the 3 folds; ties → smaller `max_depth`, then smaller `eta`, then smaller `num_boost_round`.  
**After selection:** refit on full train with winning params; then threshold search on full-train probabilities.

Optuna / large Bayesian search remains **out of scope** (diminishing returns + complexity for this n).

---

## Avoiding overfitting & common pitfalls (binding)

| Pitfall | Why it kills interviews | Mitigation in 05b |
|---------|-------------------------|-------------------|
| Random shuffle split | Future headlines train the past | Time-ordered 80/20 only |
| Tune on test / peek often | Inflated “generalization” | One test evaluation after freeze |
| Deep trees / huge rounds | Memorize 400 rows | Grid caps depth≤3, rounds≤60 |
| No regularization | Overfit noise | `subsample`/`colsample`/`reg_lambda` soft pins |
| Ignore class imbalance | Threshold/F1 nonsense | `scale_pos_weight` from **train** counts; report confusion |
| Leak labels into features | `fwd_return_5d` in X | Feature matrix = `FEATURE_NAMES` only |
| Leakage via FinBERT/yfinance redo | Train/serve skew | Consume 05a parquet; do not re-score FinBERT in train CLI |
| Quote fixture F1 as Option B | Honesty fail | Separate bundle path + `bundle_kind` |
| Early-stop using test | Hidden leakage | If early stop used, watch set ⊆ **train** only (optional: last 20% of train chronological); default = **no early stop** on final refit (soft pin: off) |
| Underspecified metrics | Can’t audit | Manifest metrics keys required below |

**Train vs test gap:** Print `|train_f1 - test_f1|`. If gap > **0.25**, still write the bundle but print `WARNING: large train/test F1 gap — possible overfit` (do not auto-fail — document in README). Soft pin threshold for warning only.

---

## MLOps — what we demonstrate (local, honest)

This is a **laptop interview lab**, not a cloud training platform. Senior signal = **reproducible artifacts + fail-closed serve**, not fake MLflow theater.

| MLOps practice | In 05b? | How |
|----------------|---------|-----|
| Versioned training data pointer | Yes | `dataset_source` + `dataset_hash` in manifest |
| Reproducible params/seed | Yes | Soft pins + `seed=42` + logged `xgb_params` / `hpo` block |
| Atomic model publish | Yes | Write tmp dir → replace `model_bundle_option_b/` |
| Train/serve contract | Yes | `feature_names` must match `FEATURE_NAMES`; gate fail-closed |
| Bundle kind / stage honesty | Yes | `bundle_kind=option_b`; env require guard |
| Local run summary | Yes | Write `artifacts/runs/option_b_train_<utc>.json` (gitignored under `artifacts/`) with metrics + winner params + paths |
| Remote experiment tracking (W&B/MLflow) | **No** | Explicit non-goal — mention in docs as future |
| Model registry / shadow deploy | **No** | Non-goal |
| CI trains Option B every PR | **No** | CI keeps fixture; train is operator/local (parquet gitignored) |

---

## Evals — what we demonstrate

| Eval layer | In 05b? | Notes |
|------------|---------|-------|
| Offline train/test classification metrics | **Yes** | precision/recall/F1 + confusion on train **and** test at frozen threshold |
| HPO inner-fold logloss | **Yes** | Logged in manifest (`hpo.fold_logloss` + mean) |
| Gate policy goldens (Guide 03) | **Keep** | Still run on **fixture** by default — proves plumbing |
| Option B end-to-end smoke | **Optional demo** | `MODEL_BUNDLE_DIR=...` + `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` — not default CI |
| Live trading PnL / backtest | **No** | Out of scope — downside gate ≠ alpha |
| LLM schema-pass rates | **No** | Separate from XGBoost train |
| Ablation (drop FinBERT feature) | **No** | Nice later; not 05b |

**Honesty rule:** Test F1 on n_test≈100 with ~16% positives is **noisy**. Report it; do not market as production risk model.

---

## Learning notes (short)

1. **Nested evaluation** — Outer time holdout for reporting; inner `TimeSeriesSplit` only on train for HPO.  
2. **Threshold ≠ booster HPO** — Select trees by logloss; choose operating point by train F1.  
3. **Train/serve skew** — Manifest feature order is the contract.  
4. **Imbalance** — `scale_pos_weight` from train; always publish confusion counts.

---

## References (paths only)

- `alphaguard/docs/2026-07-16_guide05b_option_b_train_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§6.3, §7.4–§7.6, §11, AG1–AG3)
- `alphaguard/docs/VISION.md`
- `alphaguard/docs/TRAINING_DATA.md`
- `alphaguard/scripts/build_fixture_bundle.py`
- `alphaguard/src/alphaguard/contracts/manifest.py`
- `alphaguard/src/alphaguard/contracts/decisions.py`
- `alphaguard/src/alphaguard/ml/gate.py`
- `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. Train only — no live RSS; no Option C; no FinBERT retrain.  
2. AG2 / AG3 honored via 05a labels/features.  
3. Split first — time-ordered 80/20; **no shuffle**.  
4. HPO + threshold on **train only**; one test eval after freeze.  
5. `score_kind=proba_high_risk`; `bundle_kind=option_b`.  
6. Default smoke = fixture.  
7. ≤300 lines/file preferred (hard max 400).  
8. Same-delivery docs honesty; still not v1 complete.  
9. 5-ticker coverage accepted; FB→META deferred.

---

## Soft pins (locked for Implement)

| Pin | Locked default |
|-----|----------------|
| Parquet in | `data/derived/training_events.parquet` (`--parquet` OK) |
| CLI | `scripts/train_option_b_gate.py` |
| Library | `src/alphaguard/ml/train_option_b.py` (+ helpers only if needed for ≤300 lines) |
| Bundle out | `data/derived/model_bundle_option_b/` |
| Features / label | `FEATURE_NAMES` / `label_high_risk` |
| Outer split | Time-ordered 80/20 on `published_at` |
| HPO | Grid above + `TimeSeriesSplit(n_splits=3)` on train; select by mean val **logloss** |
| Final early stop | **Off** |
| Threshold grid | `np.linspace(0.05, 0.95, 19)` on full-train probs; max F1; ties → lower threshold |
| F1 undefined | Fail closed |
| Vol veto | `false` / `null` |
| `bundle_id` / `model_version` | `option-b-downside-v1` / `0.1.0-option-b` |
| `dataset_hash` | sha256 of full feature matrix (all rows used) + labels; document in TRAINING_DATA |
| Atomic write | tmp dir → replace |
| Run summary | `artifacts/runs/option_b_train_<utc>.json` |
| Smoke | Fixture default; Option B via `MODEL_BUNDLE_DIR` → `Settings.model_bundle_dir` (`src/alphaguard/config.py`) |
| Honesty guard | `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` → fail closed if mismatch |
| Overfit warning | Warn if `|train_f1 - test_f1| > 0.25` |
| `label_window` | Exact ARCHITECTURE strings: start=`first_completed_session_close_at_or_after_event_session`, end=`close_5_trading_sessions_later` |
| `label_definition` | `fwd_return_5d < -0.03` |
| `library_versions` | Must include `xgboost`, `numpy`, `sklearn`, `python` version strings |
| Val fold score | `sklearn.metrics.log_loss` on fold probabilities |

### Manifest `metrics` / `hpo` required keys

- Counts: `n_train`, `n_test`, `n_positive_train`, `n_positive_test`  
- Threshold + train/test precision, recall, F1, TP/FP/TN/FN  
- `train_test_f1_gap`  
- `xgb_params` (winner)  
- `scale_pos_weight`  
- `hpo`: `{ "method": "timeseries_split_grid", "n_splits": 3, "space": {...}, "selection": "mean_val_logloss", "candidates_evaluated": N, "winner": {...}, "fold_logloss": [..per fold for winner..], "fold_mean_logloss": float }`  
- `hyperparam_search` = `"timeseries_split_grid_05b"`  

---

## Acceptance criteria (Implement)

- [x] CLI runs HPO + train + threshold + atomic bundle write  
- [x] Unit tests: time split; HPO never sees test indices; threshold train-only; NaN fail-closed; feature_names; require-bundle-kind guard  
- [x] Default smoke fixture; optional Option B demo documented  
- [x] Run summary JSON written under `artifacts/runs/`  
- [x] Docs honesty (VISION / ARCHITECTURE / README / TRAINING_DATA / AGENTS)  
- [x] No FinBERT in default pytest path  

---

## Ordered step checklist

All boxes start unchecked at Implement. **Do not check during Refine.**

### Phase A — Layout + load + split

- [x] **A1.** `train_option_b.py` + thin CLI.  
- [x] **A2.** Load parquet; require features/label/`published_at`; NaN fail-closed.  
- [x] **A3.** Sort by `published_at`; 80/20 split; record `train_window`.

### Phase B — HPO + final train + threshold

- [x] **B1.** Compute `scale_pos_weight` from train.  
- [x] **B2.** Run soft-pinned grid with `TimeSeriesSplit(n_splits=3)` on train; pick min mean val logloss.  
- [x] **B3.** Refit winner on full train.  
- [x] **B4.** Fit `score_threshold` on full-train probs (train-F1 max).  
- [x] **B5.** Evaluate test once; build metrics + `hpo` block; warn on large F1 gap.

### Phase C — Bundle + MLOps + gate honesty

- [x] **C1.** Atomic write model + manifest + bundle README.  
- [x] **C2.** Write `artifacts/runs/option_b_train_<utc>.json`.  
- [x] **C3.** Env-gated `bundle_kind` require in `gate.py`.  
- [x] **C4.** Document Option B demo env; smoke default unchanged.

### Phase D — Tests + docs

- [x] **D1.** Synthetic time-ordered unit tests (CI without live parquet).  
- [x] **D2.** Docs honesty updates.  
- [x] **D3.** Stop — no Optuna platform; no FB→META; no v1 claim.

---

## Verification / Definition of Done

```bash
uv run python scripts/train_option_b_gate.py
test -f data/derived/model_bundle_option_b/manifest.json
python -c "import json; m=json.load(open('data/derived/model_bundle_option_b/manifest.json')); assert m['bundle_kind']=='option_b'; assert m['metrics']['hpo']['method']=='timeseries_split_grid'; print(m['metrics']['test_f1'], m['metrics']['hpo']['winner'])"

uv run pytest -q
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke

MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b \
ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b \
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke

rg -n 'option_b|timeseries_split_grid|Option B' docs/VISION.md docs/ARCHITECTURE.md README.md docs/TRAINING_DATA.md
```

**DoD:** Bundle + HPO audit trail + metrics + docs honest + fixture smoke green.

---

## Blast radius and risks

| Risk | Mitigation |
|------|------------|
| HPO overfit to train folds | Tiny grid; logloss selection; shallow trees; warn on train/test F1 gap |
| Threshold leakage | Train-only fit |
| Fixture overwrite | Separate derived path |
| CI depends on parquet | Unit tests synthetic; live train operator-only |
| Scope into W&B/Optuna | Hard stop |

### Rollback

Delete derived Option B bundle + train run JSON; revert commits; fixture smoke must pass.

---

## Edge cases

| Case | Behavior |
|------|----------|
| Missing parquet | Fail closed + TRAINING_DATA regenerate |
| `n_pos_train==0` | Fail closed |
| NaN features | Fail closed |
| Re-run train | Atomic replace bundle |
| Require option_b + fixture path | Fail closed |
| Inner fold too small | Fail closed with clear error if a fold has <2 classes or <10 rows |

---

## Stop conditions

- Option B bundle + HPO audit + docs honesty  
- **Do not** add MLflow/W&B  
- **Do not** default CI to Option B smoke  
- **Do not** claim v1 / production risk model  

---

## Refine pass 74 notes

- Elevated HPO from “fixed only” → **nested time-grid** (senior-credible, still small).  
- Added explicit overfitting, MLOps, and eval sections.  
- Added `scale_pos_weight`, regularization soft pins, run summary artifact, F1-gap warning.  

## Verify refine pass 76 notes

- Clarified **HPO** acronym; soft-pinned `sklearn.log_loss` + tie-break includes `eta`.  
- Soft-pinned §7.6 `label_window` / `label_definition` / `library_versions`.  
- Confirmed Option B demo path: env `MODEL_BUNDLE_DIR` → `Settings.model_bundle_dir` (already exists).  
- Aligned `hpo.fold_logloss` naming.  
- **No material invent risk remaining.** Ready-check already passed — next human gate is **Authorize Implement**.

## Ready-check / Implement readiness (verify — do not inflate)

| Score | Value |
|-------|--------|
| Ready-check readiness (unchanged) | **9.1 / 10** |
| Implement readiness (pass 75) | **9.0 / 10** |
| Guide good to go as refined? | **Yes** |

**Why not 10:** Live parquet HPO runtime proof belongs to Implement — not another guide pass.
