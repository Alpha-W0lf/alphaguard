# Experiments: harness and run registry

**Status:** Harness complete · **Harness Go ≠ Model Quality Go**  
**Engineering rails:** Config-as-code matrix · ProcessPool parallel workers · Local artifacts under `artifacts/runs/studies/<study_id>/` · Leakage discipline · Local MLflow file store optional (off by default; no Databricks, no cloud training).

---

## 1. Design

1. **Floors fixed in advance.** A study declares its floors (F1, precision, AUPRC) and seeds in YAML before it runs; stop rules are set in a written plan before the run. The floors were set after the first baseline and held fixed for every later experiment.
2. **Point-in-time splits that test for leakage.** Study splits are time-ordered with a trading-day purge when session dates are present, and tests fail if a training label window crosses into the next block. The single-run trainer, `scripts/train_option_b_gate.py`, is not a study and uses a plain 80/20 cut. The audit that motivated the purge is §7.
3. **Out-of-sample selection.** Calibration, Fβ thresholds and shortlist ranking use a train-internal validation slice scored by a booster that never trained on it; the default `train_f1_max` threshold is fit on the training rows. The locked test is scored once per run, at the end, and read only by the floor check.
4. **Traceable records.** Every run records git SHA, dataset hash (checked; a mismatch fails closed), config hash, threshold method, confusion matrix and rare-event metrics ($P, R, F_1, F_\beta$, AUPRC, Brier). Run records are write-once.
5. **Enough positives to measure.** A 500-event freeze had 3 test positives, too few to compare thresholds, so the sample was expanded to 8,907 events with 233 test positives before any gate ran.
6. **Propose, then decide.** The multi-seed gate can only propose a candidate. A person makes the model-quality call.

---

## 2. Launching a Study

### 2.1 Study Configuration (`configs/studies/<name>.yaml`)

Studies are defined as declarative configs:

```yaml
study_id: harness_smoke
description: Smoke study matrix across seeds and threshold fitting methods
dataset_path: data/derived/training_events.parquet
dataset_hash: a8bdd0fbda9ce31bce28de41a66a9698baeafb3fb58b1ab8ebdc586e1b10af1c

seeds:
  - 42
  - 101

threshold_methods:
  - train_f1_max
  - train_val_fbeta_0.5

betas:
  - 0.5

calibration_methods:
  - none

max_depths:
  - 2

etas:
  - 0.1

num_boost_rounds:
  - 40

scale_pos_weights:
  - null  # auto n_neg / n_pos

split_policy: nested_time_aware_v1
train_frac: 0.8
val_frac: 0.2
enable_mlflow: false
mlflow_tracking_uri: artifacts/mlruns
```

### 2.2 Execution CLI

Run a study using parallel worker processes:

```bash
# Using the dedicated script
python scripts/run_study.py --study configs/studies/harness_smoke.yaml --workers 4

# Or via the alphaguard CLI
alphaguard study run --study configs/studies/harness_smoke.yaml --workers 4
```

Each matrix cell runs in an isolated process with its own seed and isolated model bundle directory under `artifacts/runs/studies/<study_id>/bundles/<run_id>/`.

`--walk-forward` defaults to `off` and `--economic` defaults to `off`. Those defaults leave the single 80/20 split unchanged.

#### macOS OpenMP / XGBoost crashes

On macOS, unbounded OpenMP inside libomp (pulled in by XGBoost) can SIGSEGV during study runs or pytest — classic "Python quit unexpectedly" popups with stacks in `__kmp_fork_barrier` / `__kmp_launch_worker`. Dismissing the dialog does not fix the crash; the next parallel run will hit it again.

AlphaGuard setdefaults these env vars to `1` (never overwriting a value you already set) via `apply_native_thread_limits()` before XGBoost is imported: `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, `NUMEXPR_NUM_THREADS`, `XGB_NUM_THREAD`. On Darwin the CLI also defaults `--workers` to **1** (laptop-safe). Other platforms still default to 4. Pass `--workers N` to override; when `workers>1`, ProcessPool already uses `spawn` (not fork).

### 2.3 Phase B (walk-forward + economic stub)

One seed, still on freeze `534a341a…`. Threshold policy for this command is `train_f1_max`. Model hyperparameters, calibration, and beta are read from the YAML and the YAML is not edited. Walk-forward folds stay inside the dev block. The locked test is scored once. Promotion prints `candidate` or `no candidate` from the unchanged floors. It does not claim a quality decision.

```bash
python scripts/run_phase_b.py run \
  --config configs/studies/go_gate_seeds_7_123.yaml \
  --freeze 534a341a \
  --seed 0 \
  --walk-forward expanding4 \
  --economic on \
  --cost-fp 1 \
  --cost-fn 10 \
  --out runs/phaseb_YYYY-MM-DD/seed0
python scripts/run_phase_b.py summarize runs/phaseb_YYYY-MM-DD
python scripts/run_phase_b.py promote runs/phaseb_YYYY-MM-DD
```

Optional blocks `walk_forward` and `economic` are omitted from the run JSON when they were not run (`schema_version` `1.1` only when a block is present). Stub costs are unitless (`label: stub`).

---

## 3. Run Registry Layout

Artifacts are persisted locally in standard JSON files:

```
artifacts/runs/studies/<study_id>/
  study.json                 # Parent study record (git SHA, dataset_hash, completed runs, promotion)
  runs/<run_id>.json         # Child run records (config_hash, threshold, metrics, confusion, timings)
  bundles/<run_id>/          # Isolated XGBoost model bundle + manifest.json per cell
  compare.md                 # Generated Markdown comparison table
  compare.csv                # Generated CSV comparison table
```

### Required Fields Captured in Child Run JSON:
- `git_sha`: Launch commit HEAD.
- `dataset_hash`: SHA-256 of the training data snapshot (fails closed on mismatch).
- `config_hash`: Fingerprint of canonicalized cell configuration.
- `seed`: Random seed.
- `threshold_method`: Fitting method (e.g. `train_f1_max`, `train_val_fbeta_0.5`).
- `calibration_method`: Calibration method (`none`, `platt`, `isotonic` fit train/val only).
- `metrics`: Train, val, and locked-test metrics ($P, R, F_1, F_\beta, \text{AUPRC}, \text{Brier}$, prevalence). Val metrics come from an auxiliary booster trained on the first part of train only, so they are out-of-sample.
- `confusion`: Exact TP/FP/TN/FN counts on locked test.
- `wall_time_s`: Elapsed training seconds.
- `aborted`: Boolean flag indicating whether an experiment aborted (e.g., a single-class validation slice, which fails the run closed).

---

## 4. Comparing Results

Generate comparison tables anytime from a study directory:

```bash
python scripts/compare_study.py --study-dir artifacts/runs/studies/harness_smoke --sort-by test_f1
# or
alphaguard study compare --study-dir artifacts/runs/studies/harness_smoke
```

The resulting `compare.md` sorts candidate configurations by held-out test performance without obscuring test counts or false positives:

| Run ID | Config | Seed | Method | Calib | Threshold | Test F1 | Test P | Test R | Test Fβ | AUPRC | Brier | Confusion (TP/FP/TN/FN) | N+ Test | Wall (s) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `run_000_...` | `e2a4f109` | 42 | train_f1_max | none | 0.500 | 0.0870 | 0.0500 | 0.3333 | 0.0610 | 0.1240 | 0.1820 | 1/19/78/2 | 3 | 0.12 | OK |

---

## 5. Leakage Discipline & Promotion Gates

1. **Outer Split:** Held-out test split is strictly locked and scored **once** per run after the booster, calibration, and threshold are frozen. Test rows are never passed to HPO, calibrators, or threshold fitters.
2. **Inner Split:** Threshold fitting and probability calibration execute strictly on train or train-internal validation splits.
3. **Promotion Policy & Three Gates:**
   - See dedicated [`docs/PROMOTION_POLICY.md`](./PROMOTION_POLICY.md).
   - **Three Gates:** (1) Harness Go (Engineering), (2) Model Quality Go (human review), (3) Economic Claim (Future / Not Claimed).
   - **Automated Multi-Seed Gate:** The study runner extracts the top-$k$ distinct hyperparameter candidates ranked on validation metrics (`shortlist_top_k = 3`), schedules evaluation runs on extra seeds (`[7, 123]`), and checks locked floors:
     - **Test F1 ≥ 0.30**
     - **Test Precision ≥ 0.25**
     - **Test AUPRC ≥ 0.18**
   - **Zero Soft Misses:** If any seed fails any floor, `promotion_decision` is marked `rejected`. Only if all extra seeds clear all floors does the harness propose `candidate`.
   - **Propose ≠ Claim:** An automated `candidate` decision is a proposal for human audit. A person makes the model-quality call; the shipped threshold method is `train_f1_max`.

---

## 6. Multi-Seed Study Configuration Example

```yaml
# configs/studies/promotion_demo.yaml
study_id: promotion_demo
description: Multi-seed promotion gate demonstration with locked floors
dataset_path: data/derived/training_events.parquet

seeds:
  - 42

threshold_methods:
  - train_f1_max
  - train_val_fbeta_0.5

betas:
  - 0.5

calibration_methods:
  - none

max_depths:
  - 2

etas:
  - 0.1

num_boost_rounds:
  - 20

scale_pos_weights:
  - null

split_policy: nested_time_aware_v1
train_frac: 0.8
val_frac: 0.2
enable_mlflow: false
mlflow_tracking_uri: artifacts/mlruns

promotion:
  enabled: true
  shortlist_top_k: 3
  extra_seeds:
    - 7
    - 123
  floors:
    f1: 0.30
    precision: 0.25
    auprc: 0.18
  sort_by: val_f1
```

Executing this configuration runs primary discovery, automatically evaluates shortlisted configurations across seeds 7 and 123, updates `study.json` with multi-seed rollups, and appends a "Promotion Gate" report to `compare.md`.

---

## 7. Leakage audit (2026-09-25)

The harness audits its own splits. On the 8,907-event freeze it recomputed every label from `fwd_return_5d < -0.03` (0 mismatches), checked every row's as-of times (0 violations) and looked for construction duplicates (0). It also checked whether any training row's 5-day label window reaches into the next block, and found that it did: 107 same-ticker rows on the walk-forward boundaries and 92 on the locked-test boundary (`runs/leakage_audit_2026-09-25/`).

The fix is a trading-day purge on the study harness's walk-forward and locked-test splits: training rows stop before the next block's first feature session, so no training label window reaches into the next block or the locked test. Tests fail if one does (`tests/test_phase_c_audit.py`). The train-internal validation slice used for calibration and thresholds is not purged, and neither is the 80/20 cut in the single-run trainer (`scripts/train_option_b_gate.py`). Affected configurations were re-run with the purge. These records come from the retired 5-feature freeze `534a341a…`. To run the audit on a current rebuild (built as in [`TRAINING_DATA.md`](./TRAINING_DATA.md); the parquet is not committed), pass that rebuild's hash prefix: `uv run python scripts/audit_phase_c.py --freeze <prefix>`.

The audit's run records are in `runs/leakage_audit_2026-09-25/`. Study ids in `runs/` were renamed after the runs (2026-10-18). The public repo is a snapshot of the development history; the dataset hash in each record identifies the exact data.
