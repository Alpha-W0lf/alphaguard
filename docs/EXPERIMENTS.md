# MLOps Experiment Harness & Run Registry (JH-63.2)

**Status:** Implementation complete (JH-63.2) · **Harness Go ≠ Model Quality Go**  
**Engineering rails:** Config-as-code matrix · ProcessPool parallel workers · Local artifacts under `artifacts/runs/studies/<study_id>/` · Leakage discipline · Local MLflow file store optional (off by default; no Databricks, no cloud training).

---

## 1. Executive Summary & Engineering Posture

AlphaGuard enforces strict point-in-time discipline and leakage guards across both inference and training. In ticket **JH-63.1**, an A/B evaluation of precision-weighted thresholding (`train_val_fbeta_0.5` at $\beta=0.5$) vs the baseline `train_f1_max` on the frozen `a8bdd0fb...` snapshot resulted in an honest **Fail** on the locked held-out test split ($F_1 = 0.0$ vs baseline $F_1 \approx 0.087$). Root-cause analysis revealed that with only $n_{\text{positive, test}} = 3$, threshold-only adjustments on a rare class are noise.

The solution is not to hide the Fail or fabricate metrics; it is senior engineering discipline:
1. **JH-63.2 (This Harness):** Build a portable, leak-free, parallel experiment matrix runner and run registry that systematically records parent studies and child runs with git SHAs, dataset hashes, configuration hashes, threshold methods, confusion matrices, and rare-event metrics ($P, R, F_1, F_\beta, \text{AUPRC}, \text{Brier}$).
2. **JH-63.3 (Data Scaling):** Scale the sample locally to reach statistical power ($\ge 30$, stretch $\ge 50$ locked-test positives under the frozen $-3\%/5d$ downside label) before evaluating model promotion.
3. **JH-63.3 (Data Scaling — executed):** Full-pool freeze $n=8907$, `dataset_hash=534a341a…`, `n_positive_test=233`. Re-baseline `train_f1_max` locked-test $F_1 \approx 0.2108$ (see [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md) § JH-63.3). JH-63.1 Fail stays published. **Model Quality Go not claimed.**
4. **Acceptance Distinction:** Harness acceptance (running reproducible parallel sweeps without cross-talk or leakage) is decoupled from model quality acceptance. Harness Go ≠ Model Quality Go.

---

## 2. Launching a Study

### 2.1 Study Configuration (`configs/studies/<name>.yaml`)

Studies are defined as declarative configs:

```yaml
study_id: jh63_2_smoke
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
python scripts/run_study.py --study configs/studies/jh63_2_smoke.yaml --workers 4

# Or via the alphaguard CLI
alphaguard study run --study configs/studies/jh63_2_smoke.yaml --workers 4
```

Each matrix cell runs in an isolated process with its own seed and isolated model bundle directory under `artifacts/runs/studies/<study_id>/bundles/<run_id>/`.

`--walk-forward` defaults to `off` and `--economic` defaults to `off`. Those defaults leave the single 80/20 split unchanged.

### 2.3 Phase B (walk-forward + economic stub)

One seed, still on freeze `534a341a…`. Threshold policy for this command is `train_f1_max`. Model hyperparameters, calibration, and beta are read from the YAML and the YAML is not edited. Walk-forward folds stay inside the dev block. The locked test is scored once. Promotion prints `candidate` or `no candidate` from the unchanged floors. It does not claim a quality decision.

```bash
python scripts/run_phase_b.py run \
  --config configs/studies/jh63_go_gate_seeds_7_123.yaml \
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
- `metrics`: Train, val, and locked-test metrics ($P, R, F_1, F_\beta, \text{AUPRC}, \text{Brier}$, prevalence).
- `confusion`: Exact TP/FP/TN/FN counts on locked test.
- `wall_time_s`: Elapsed training seconds.
- `aborted`: Boolean flag indicating whether an experiment aborted (e.g., single-class val).

---

## 4. Comparing Results

Generate comparison tables anytime from a study directory:

```bash
python scripts/compare_study.py --study-dir artifacts/runs/studies/jh63_2_smoke --sort-by test_f1
# or
alphaguard study compare --study-dir artifacts/runs/studies/jh63_2_smoke
```

The resulting `compare.md` sorts candidate configurations by held-out test performance without obscuring test counts or false positives:

| Run ID | Config | Seed | Method | Calib | Threshold | Test F1 | Test P | Test R | Test Fβ | AUPRC | Brier | Confusion (TP/FP/TN/FN) | N+ Test | Wall (s) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `run_000_...` | `e2a4f109` | 42 | train_f1_max | none | 0.500 | 0.0870 | 0.0500 | 0.3333 | 0.0610 | 0.1240 | 0.1820 | 1/19/78/2 | 3 | 0.12 | OK |

---

## 5. Leakage Discipline & Promotion Gates

1. **Outer Split:** Held-out test split is strictly locked and scored **once** per run after the booster, calibration, and threshold are frozen. Test rows are never passed to HPO, calibrators, or threshold fitters.
2. **Inner Split:** Threshold fitting and probability calibration execute strictly on train or train-internal validation splits.
3. **Promotion Policy & Three Gates (JH-AG-93.1 / JH-AG-93.2):**
   - See dedicated [`docs/PROMOTION_POLICY.md`](./PROMOTION_POLICY.md).
   - **Three Gates:** (1) Harness Go (Engineering), (2) Model Quality Go (Human Review / Tom Chacko), (3) Economic Claim (Future / Not Claimed).
   - **Automated Multi-Seed Gate:** The study runner automatically extracts top-$k$ distinct hyperparameter candidates (`shortlist_top_k = 3`), schedules evaluation runs on extra seeds (`[7, 123]`), and checks locked floors:
     - **Test F1 ≥ 0.30**
     - **Test Precision ≥ 0.25**
     - **Test AUPRC ≥ 0.18**
   - **Zero Soft Misses:** If any seed fails any floor, `promotion_decision` is marked `rejected`. Only if all extra seeds clear all floors does the harness propose `candidate`.
   - **Propose ≠ Claim:** An automated `candidate` decision is a proposal for human audit. Model Quality Go is currently **UNCLAIMED**; shipped default remains `train_f1_max`.

---

## 6. Multi-Seed Study Configuration Example

```yaml
study_id: jh93_promotion_demo
description: Multi-seed promotion gate evaluation on locked test
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
  - isotonic

max_depths:
  - 2

etas:
  - 0.1

num_boost_rounds:
  - 40

scale_pos_weights:
  - null

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
  sort_by: test_f1
```

Executing this configuration runs primary discovery, automatically evaluates shortlisted configurations across seeds 7 and 123, updates `study.json` with multi-seed rollups, and appends a "Promotion Gate" report to `compare.md`.
