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

---

## 7. Phase C — labels and data audit (2026-09-25)

Audit of freeze `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` (n=8907). The Phase B Fail on this freeze stands: harness `78b85bf6`, 0/5 seeds clear the unchanged floors, no candidate. The Phase B summary stays as recorded. **Model Quality Go remains UNCLAIMED.**

Local evidence (not committed): `runs/phasec_2026-09-25/audit/` (`gates.md`, `c1_labels.json`, `c2_folds.json`, `c3_leakage.json`, `c4_rules.json`). Re-run: `uv run python scripts/audit_phase_c.py`.

### Gate (a) — fired

C1 recomputed `label_high_risk` from `fwd_return_5d < -0.03` on every row: **0 mismatches**. As-of check: **0 violations**. Construction duplicates on `(ticker, ET date, normalized headline)`: **0**. Repeated `(ticker, feature_as_of)` headlines: 7822 rows under the headline-level dedup rule.

The recorded 5-global-row embargo is short of 5 feature sessions on **5/5 boundaries** and leaves **229** train rows whose 5-session label window reaches the next block (fold gaps 24, 6, 33, 70; locked test 96, and that boundary had no row gap).

The trading-day purge in `study_walkforward.py` moves those train ends back. On this freeze the purged gaps are 29, 11, 38, 75, and 96 rows, each covering at least 6 feature sessions, and **overlap rows = 0**. Frames without session dates still use the 5-row gap, so the Phase B unit tests keep that protocol.

### Gate (b) — fired

| slice | n | prevalence | verdict | evidence |
| --- | ---: | ---: | --- | --- |
| fold 0 | 1068 | 0.1667 | artifact | 177/178 positives are NVDA (99.4%). Dates 2016-08-19 to 2018-03-12. The archive in that window is NVDA and QQQ only |
| fold 1 | 1069 | 0.2806 | regime | NVDA 48%, GOOGL 29%, QQQ 23%. Same-day QQQ forward return median −3.2% on 97% of positives. Dates 2018-03-12 to 2018-12-19 |
| fold 2 | 1069 | 0.1759 | regime | GOOGL 60%, NVDA 37%. QQQ forward median −2.1% on 51% of positives |
| fold 3 | 1069 | 0.1731 | regime | NVDA 51%, GOOGL 38%. QQQ forward median −8.2% (Feb 2020) |
| locked test | 1782 | 0.1308 | regime | Six tickers. QQQ forward median −9.5%. Date range only; no per-row label edits |

Fold 1 is the high-prevalence fold (0.2806). Positives are spread across three tickers and line up with the late-2018 market drawdown. AUPRC / prevalence from the Phase B run JSON is diagnostic only (`c2_folds.json`).

### Gate (c) — fired (misaligned)

Rules spec `return_5d_prior < -0.03`. Veto-set positive rate is higher on **2/4** folds (folds 2 and 3). Folds 0 and 1 go the other way. The locked test is higher (0.368 vs 0.085). The 3/4 rule counts the four folds. Verdict: **misaligned**.

### WP-C5 — fired, no new freeze

Pre-registered change, decided before any new hash:

- Fired gates: (a), (b), and (c).
- Label definition stays `fwd_return_5d < -0.03`. No second label. AG2 keeps the prior-return rule out of the target. Fold 0's single-ticker positives are the archive (no AAPL, AMZN, or META rows before 2020), not a threshold to retune.
- Defect fix that landed: when session dates exist, train rows stop before the next block's feature session. Hyperparameters, feature names, and the booster family are unchanged.
- Old freeze `534a341a…`. Phase B harness commit `78b85bf6`. Floors stay F1 ≥ 0.30, P ≥ 0.25, AUPRC ≥ 0.18. Seeds 0–4, `--walk-forward expanding4`, `--economic on`, `--cost-fp 1`, `--cost-fn 10` stay the comparison flags.
- Comparison layout, if a later run is authorized: old `runs/phaseb_2026-09-25/SUMMARY.md` vs the new summary, per seed, per fold, and on the locked test.
- No new parquet. The dataset hash is SHA-256 of the feature matrix and labels. The embargo is not in those bytes. Rebuilding with `scripts/build_training_events.py` would not encode the purge and could move adjusted closes. Hash remains `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`.

The five Phase B seeds were not re-run. A re-run on this commit would change train membership, so it would not be a freeze-only comparison.

---

## 8. Phase C Go-gate re-run (2026-09-25) — FAIL, Go UNCLAIMED

Post–Phase-C multi-seed Go gate on freeze `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` after PR #16 (`ebfb8c2`, session-horizon purge on HEAD). Floors unchanged: F1 ≥ 0.30, Precision ≥ 0.25, AUPRC ≥ 0.18. **Model Quality Go remains UNCLAIMED.** Phase B Fail summary above stands.

| field | value |
| --- | --- |
| Date (CDT) | 2026-09-25 13:08 |
| Harness SHA | `ebfb8c249440c39747b7581da4ca94782e3dfc2a` |
| Freeze hash | `534a341a…` (`dataset_hash_match: true`) |
| Study id | `jh63_go_gate_phase_c_534a` |
| Config | `configs/studies/jh63_go_gate_phase_c_534a.yaml` |
| CLI | `uv run python scripts/run_study.py --study configs/studies/jh63_go_gate_phase_c_534a.yaml --workers 2` |
| Walk-forward | `off` (default nested split) |
| Promotion decision | `rejected` |
| Gate overall | **FAIL** |
| `model_quality_go_claimed` | `false` |

Per-seed locked-test floors (matrix C winner hparams: `train_val_fbeta_0.5`, β=1.0, isotonic, depth 2, η=0.1, rounds 40, spw 2):

| seed | role | F1 | P | AUPRC | floor |
| ---: | --- | ---: | ---: | ---: | --- |
| 42 | primary | 0.3658 | 0.2787 | 0.2087 | PASS |
| 7 | extra | 0.2664 | 0.1711 | 0.1946 | FAIL (F1, P) |
| 123 | extra | 0.3227 | 0.2263 | 0.1963 | FAIL (P) |

Artifacts: `artifacts/runs/studies/jh63_go_gate_phase_c_534a/{study.json,compare.md,go_gate_summary.json}`.

**Purge note:** Phase C trading-day purge in `study_walkforward.py` activates for `--walk-forward expanding4` (and WF folds). This Go-gate used the documented nested path (`walk_forward=off`), so train membership matches the prior nested Go-gate (`jh63_go_gate_seeds_7_123`); seed 7/123 metrics are unchanged. A WF expanding4 re-run was not part of this authorized CLI.

Harness proposal only (`rejected`). **Do not claim Model Quality Go.**

---

## 9. Phase B re-run with Phase C purge (2026-09-25) — no candidate, Go UNCLAIMED

Authorized WF expanding4 comparison on freeze `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` after the session-horizon purge landed (PR #16 / HEAD includes PR #17). **This IS the purge-on comparison** vs old `runs/phaseb_2026-09-25/` (pre-purge `embargo_rows=5`). Floors unchanged: F1 ≥ 0.30, P ≥ 0.25, AUPRC ≥ 0.18. Seeds 0–4. **Model Quality Go remains UNCLAIMED.** Fail stays Fail.

| field | value |
| --- | --- |
| Date (CT) | 2026-09-25 ~1:13 PM |
| Harness SHA | `f56a870c848d1486acad9c0d15616e6546cfcdc4` |
| Freeze hash | `534a341a…` (`dataset_hash_match: true`) |
| Config | `configs/studies/jh63_go_gate_seeds_7_123.yaml` (matrix C winner hparams) |
| Flags | `--walk-forward expanding4 --economic on --cost-fp 1 --cost-fn 10` |
| Purge | ON — `trading_day_horizon`; fold gaps 29, 11, 38, 75; locked-test drop 96 (`train_end=7029` vs boundary 7125) |
| Promote | **no candidate** (0/5 seeds clear floors) |
| `model_quality_go_claimed` | `false` |

Per-seed locked-test floors vs old Phase B (`runs/phaseb_2026-09-25`):

| seed | old F1 | new F1 | old P | new P | old AUPRC | new AUPRC | floors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.3006 | 0.2489 | 0.2115 | 0.1452 | 0.1924 | 0.1945 | N / N |
| 1 | 0.2517 | 0.2347 | 0.1531 | 0.1366 | 0.1969 | 0.1676 | N / N |
| 2 | 0.2585 | 0.2408 | 0.1586 | 0.1397 | 0.1972 | 0.1597 | N / N |
| 3 | 0.2564 | 0.2465 | 0.1601 | 0.1527 | 0.1919 | 0.1670 | N / N |
| 4 | 0.2540 | 0.2451 | 0.1526 | 0.1498 | 0.1809 | 0.1727 | N / N |

Train membership (seed 0 folds): old gaps all 5 → new 29/11/38/75; `n_positive_train` 1273 → 1201; locked-test `n_positive_test` unchanged at 233; `n_dev` / `locked_test_start` still 7125.

Local artifacts (gitignored): `runs/phaseb_phasec_2026-09-25/{SUMMARY.md,PROMOTE.txt,driver.log,seed*/}`. Old `runs/phaseb_2026-09-25/` left intact.

Harness proposal only (`no candidate`). **Do not claim Model Quality Go.**

