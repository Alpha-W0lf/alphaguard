# Dev Guide 05b — Option B XGBoost train + `bundle_kind=option_b`

**Date:** 2026-07-16  
**Repo:** `alphaguard`  
**Work item:** Guide 05b — train downside-risk XGBoost on Guide 05a parquet; write Option B model bundle  
**Stage that authored this:** Write-dev-guide (pass 73)  
**Status:** **Draft guide** — ready for Refine-dev-guide / Ready-check; **no Implement yet**

**Context SSOT:** `alphaguard/docs/2026-07-16_guide05b_option_b_train_context_summary.md`  
**Upstream dataset:** Guide 05a Review-shippable — `docs/TRAINING_DATA.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`  
**Prerequisite:** Regenerable `data/derived/training_events.parquet` (or documented regenerate). Guides 01–04 shippable. Fixture gate remains default smoke.

---

## Objective

Train a reproducible **XGBoost binary classifier** that emits `downside_risk_score = P(label_high_risk=1)`, fit **`score_threshold` on train only** (train-F1 max), write a loadable bundle with `bundle_kind=option_b`, and update docs honesty — **without** claiming v1 Done or switching default smoke off the fixture bundle.

**Success signal:** Operator runs one CLI; gets `data/derived/model_bundle_option_b/`; can point `MODEL_BUNDLE_DIR` at it for a demo; default `make smoke` still uses fixture; README shows train/test metrics labeled Option B.

---

## Learning notes — training vs “fine-tuning” (binding mental model)

### What this guide is **not**

| Term people say | What we do in 05b |
|-----------------|-------------------|
| LLM fine-tuning | **Do not** fine-tune Gemma/Ollama or any generative LLM |
| FinBERT fine-tuning | **Do not** update FinBERT weights — Guide 05a already scored headlines with frozen `ProsusAI/finbert` |
| End-to-end deep learning | **Do not** train a neural net on raw text |

### What this guide **is**

**Supervised tabular training:** features already in parquet (`FEATURE_NAMES`) → XGBoost → probability → deterministic gate policy (ARCHITECTURE §7.4).

Industry names for interview fluency:

1. **Train/serve skew** — Serving must use the same feature order/dtypes as the manifest.  
2. **Temporal leakage** — No random shuffle; time-ordered split; never tune or fit thresholds on the final test fold.  
3. **Nested evaluation** — Outer time holdout for reporting; any hyperparameter search only on **train** (inner time folds).  
4. **Calibration vs threshold** — We use raw `predict_proba` + a fitted threshold (train-F1). Full probability calibration (Platt/isotonic) is **out of scope** for 05b.  
5. **Class imbalance** — ~16% positive in live parquet; report confusion counts; do not fake balance by shuffling across time.

### Data collection (already Guide 05a — do not redo)

Locked practices we rely on (do not reopen without human):

- Static Kaggle archive + license recorded (CC0)  
- Universe filter + dedup + stratified sample + as-of joins (AG3)  
- Forward-downside label only (AG2)  
- FinBERT offline batch only  
- Raw dump + parquet gitignored; regenerate documented  

05b **consumes** that parquet; it does not re-collect news.

### Hyperparameter handling — modern practice for **this** n≈500 setting

| Practice | Why | 05b soft pin |
|----------|-----|--------------|
| Prefer **simple fixed defaults** for first shippable Option B bundle | Large grids on n≈400 train rows overfit; interviewers prefer honest small models | **Fixed soft-pinned params** (below) |
| If search later: **time-ordered inner CV on train only** (e.g. `TimeSeriesSplit`), never touch final test | Nested CV / purged CV family for temporal data | **Out of 05b Implement** — optional Guide 05c / later |
| Fit **decision threshold** separately on train probs (ARCHITECTURE already locks train-F1 max) | Threshold ≠ booster hyperparams | **In scope** |
| Log params + metrics into manifest | Reproducibility / audit | **In scope** |
| Do not Optuna/Bayesian-search in 05b | Extra surface + leakage risk for tiny n | **Parked** |

**Soft-pinned XGBoost defaults (first Option B train):**

```text
objective=binary:logistic
eval_metric=logloss
max_depth=3
eta=0.1
num_boost_round=50
seed=42
```

Slightly more capacity than the synthetic fixture (`max_depth=2`, 20 rounds) because we have real rows — still conservative.

---

## References (paths only)

- `alphaguard/docs/2026-07-16_guide05b_option_b_train_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§6.3, §7.4–§7.6, §11, AG1–AG3)
- `alphaguard/docs/VISION.md` (Option B / Minimum Viable)
- `alphaguard/docs/TRAINING_DATA.md`
- `alphaguard/scripts/build_fixture_bundle.py` (pattern only — fixture)
- `alphaguard/src/alphaguard/contracts/manifest.py`
- `alphaguard/src/alphaguard/contracts/decisions.py` (`FEATURE_NAMES`)
- `alphaguard/src/alphaguard/ml/gate.py`
- `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **Train only** — no live RSS; no Option C (Agent 1 labels); no FinBERT retrain.  
2. **AG2** — label is forward downside only; never OR volatility into the label.  
3. **Split first** — sort by `published_at`; first 80% train / last 20% test; **no shuffle**.  
4. **Threshold on train only** — `threshold_fitting=train_f1_max`; freeze into manifest; evaluate test with frozen threshold.  
5. **`score_kind=proba_high_risk`** — XGBoost `predict` on binary:logistic (proba).  
6. **`bundle_kind=option_b`** — never write Option B metrics into the fixture bundle path.  
7. **Default smoke stays fixture** — Option B demos use `MODEL_BUNDLE_DIR`.  
8. Prefer ≤300 lines/file (hard max 400) for new modules.  
9. Same-delivery docs honesty — Option B trained with metrics; still not “v1 complete.”  
10. 5-ticker parquet coverage accepted (honesty in TRAINING_DATA); FB→META deferred.

---

## Soft pins (locked for Implement — do not reopen without human)

| Pin | Locked default |
|-----|----------------|
| Parquet in | `data/derived/training_events.parquet` (`--parquet` override OK) |
| CLI | `scripts/train_option_b_gate.py` (thin) |
| Library home | `src/alphaguard/ml/train_option_b.py` (+ tiny helpers only if ≤300 lines) |
| Bundle out | `data/derived/model_bundle_option_b/` |
| Features | Exactly `FEATURE_NAMES` order from `contracts/decisions.py` |
| Label column | `label_high_risk` |
| Split | Time-ordered 80/20 on `published_at` |
| XGBoost params | Soft-pinned block above |
| Hyperparam search | **None in 05b** — fixed defaults; document nested time-CV as future work |
| Threshold grid | `np.linspace(0.05, 0.95, 19)` on **train** probs; maximize F1; ties → lower threshold |
| F1 undefined | **Fail closed** with clear error |
| Vol veto | `vol_veto_enabled=false`, `vol_veto_threshold=null` |
| `bundle_id` | `option-b-downside-v1` |
| `model_version` | `0.1.0-option-b` |
| `dataset_source` | Kaggle id string from parquet `source_dataset_id` (or const) |
| `dataset_hash` | sha256 of train+test feature matrix bytes + labels (document algorithm in TRAINING_DATA) |
| Atomic write | Write to `*.tmp` dir then replace bundle dir |
| Default smoke | Fixture path unchanged |
| Option B demo | `MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b` |
| Honesty guard | If `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` is set, gate load **fails closed** when manifest `bundle_kind != option_b` (small additive check in `gate.py`) |

### Manifest metrics (required keys)

At minimum in `manifest.metrics`:

- `n_train`, `n_test`, `n_positive_train`, `n_positive_test`  
- `score_threshold`  
- `train_precision`, `train_recall`, `train_f1`, `train_tp`, `train_fp`, `train_tn`, `train_fn`  
- `test_precision`, `test_recall`, `test_f1`, `test_tp`, `test_fp`, `test_tn`, `test_fn`  
- `xgb_params` (dict copy of soft-pinned params + `num_boost_round`)  
- `hyperparam_search` = `"none_fixed_soft_pin_05b"`  

---

## Acceptance criteria (Implement must meet)

- [ ] CLI trains from parquet; writes Option B bundle + valid `manifest.json`  
- [ ] Unit tests: time split order; threshold uses train only; NaN fail-closed; feature_names match  
- [ ] Loading via `MODEL_BUNDLE_DIR` works; default smoke still fixture  
- [ ] Optional `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` fail-closed path tested  
- [ ] Docs: VISION Option B row / ARCHITECTURE `ml/train` / README / TRAINING_DATA show train landed + metrics; fixture ≠ Option B  
- [ ] No FinBERT import on default pytest path; no 05a rebuild  

---

## Ordered step checklist

All boxes start unchecked. **Do not check in Write-dev-guide.**

### Phase A — Layout + load

- [ ] **A1.** Add `src/alphaguard/ml/train_option_b.py` + thin `scripts/train_option_b_gate.py`.  
- [ ] **A2.** Load parquet; require `FEATURE_NAMES` + `label_high_risk` + `published_at`; fail closed on missing/NaN features.  
- [ ] **A3.** Sort by `published_at`; split 80/20; record `train_window` start/end ISO from train rows.

### Phase B — Train + threshold

- [ ] **B1.** Train XGBoost with soft-pinned params on train only.  
- [ ] **B2.** Fit `score_threshold` on train probs (train-F1 max).  
- [ ] **B3.** Score test with **frozen** threshold; compute metrics dict.  
- [ ] **B4.** If train F1 undefined → fail closed.

### Phase C — Bundle + gate honesty

- [ ] **C1.** Atomic write `model.json` + `manifest.json` (`bundle_kind=option_b`) + short README in bundle dir.  
- [ ] **C2.** Add env-gated `bundle_kind` require check in `gate.py` (soft pin).  
- [ ] **C3.** Document Option B demo env in TRAINING_DATA / README; smoke default unchanged.

### Phase D — Tests + docs

- [ ] **D1.** Unit tests with tiny synthetic time-ordered frame (no live parquet required in CI).  
- [ ] **D2.** Update VISION / ARCHITECTURE / README / TRAINING_DATA / AGENTS honesty.  
- [ ] **D3.** Stop. Do **not** claim v1 complete; do **not** enable Optuna; do **not** FB→META.

---

## Verification / Definition of Done

```bash
# From alphaguard/ — parquet must exist (or regenerate via Guide 05a):
uv run python scripts/train_option_b_gate.py
test -f data/derived/model_bundle_option_b/manifest.json
test -f data/derived/model_bundle_option_b/model.json
python -c "import json; m=json.load(open('data/derived/model_bundle_option_b/manifest.json')); assert m['bundle_kind']=='option_b'; print(m['metrics'])"

uv run pytest -q
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke   # still fixture

# Optional Option B demo (not default CI):
MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b \
ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b \
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke

rg -n 'option_b|Option B|train_option_b' docs/VISION.md docs/ARCHITECTURE.md README.md docs/TRAINING_DATA.md
rg -n 'finbert|ProsusAI' src/alphaguard/ml/features.py || true   # still FinBERT-free
```

**DoD:** Bundle green; metrics printed; docs honest; smoke fixture default; no hyperparam search theater; Guide 05c nested tuning not started.

---

## Blast radius and risks

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| Overfitting tiny n | Misleading test F1 | Fixed small trees; honest metrics; no search on test |
| Threshold leakage | Fake gate quality | Train-only fit |
| Overwriting fixture | Break Guides 01–04 | Separate derived path |
| Claiming LLM fine-tune | Interview confusion | Docs learning notes |
| Scope into Optuna/FB alias | Calendar burn | Hard stop |

### Rollback

Delete `data/derived/model_bundle_option_b/`; revert train commits; smoke must pass on fixture.

---

## Edge-case handling

| Case | Required behavior |
|------|-------------------|
| Missing parquet | Fail closed + point to TRAINING_DATA regenerate |
| NaN features | Fail closed |
| Zero positives in train | Fail closed (F1 undefined) |
| Re-run train | Atomic replace bundle |
| `ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b` + fixture path | Fail closed |
| Class imbalance | Report counts; do not rebalance by shuffling time |

---

## Stop conditions

- Option B bundle + docs honesty landed  
- **Do not** start nested hyperparam search guide unless human authorizes  
- **Do not** switch default smoke to Option B  
- **Do not** claim v1 / alpha complete  

---

## Ready for Ready-check?

**Yes**, after one Refine-dev-guide pass if soft pins need tightening. Write-dev-guide readiness from context was **8.7 / 10**; this guide locks the soft pins that blocked 10.

**Recommended next stage:** `Refine-dev-guide` (one pass) **or** `Ready check before code` if Tom accepts soft pins as written.
