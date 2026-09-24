# Finance honesty — what AlphaGuard claims (and does not)

**Audience:** risk / research readers and interviewers who skim for trading claims.  
**Scope:** docs honesty only. Not a production risk model. Not brokerage / PnL / Lowd Capital.

## Claims we make

- **Bounded minimum viable build** (guides 01–08) is complete for the locked **local + CI** finish line: replay-first smoke, optional Compose Kafka+Qdrant, Option B **lab** train path, thin RSS poll, fail-open LangSmith/Phoenix adapters when configured.
- Agent 2 is a **downside-risk veto gate** (score + deterministic policy), not an alpha / return-forecasting product.
- **Look-ahead / as-of discipline** is binding: features stop at `feature_as_of`; retrieval requires `available_at <= published_at`. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) §8 and `tests/test_asof.py`.

## Claims we do **not** make

| Topic | Honesty |
|-------|---------|
| Gate ≠ alpha | Approve/reject is a **risk veto**, not a signal that the idea is profitable. |
| Costs / slippage / PnL | **Omitted on purpose** — this is a veto gate lab, not an execution strategy. Do not invent backtest PnL claims. |
| Production risk model | Lab-scale ~500-event Option B train; default smoke uses `bundle_kind=fixture` plumbing only. |
| Live eval completeness | No required live-Ollama numeric schema-pass rates; Yahoo RSS may flake; not 24/7 SRE. |

## Option B lab metrics (local manifest — regenerate may differ)

Quoted from a local `data/derived/model_bundle_option_b/manifest.json` (`bundle_kind=option_b`, created `2026-07-21T20:50:31Z` after archive-alias rebuild). **Not committed**; retrain locally via `scripts/train_option_b_gate.py`. Honest zeros / weak holdout are allowed and expected at this scale.

| Split | n | F1 | Precision | Recall | Confusion (TP/FP/TN/FN) |
|-------|---|----|-----------|--------|-------------------------|
| Train | 400 | ≈0.693 | ≈0.590 | ≈0.838 | 62 / 43 / 283 / 12 |
| Test | 100 | **≈0.087** | 0.05 | ≈0.333 | 1 / 19 / 78 / 2 |

Notes: `n_positive_test=3` — test F1 remains **noisy / weak**, not hidden. Prior pre-alias manifest (2026-07-17) had test F1 = 0.0 on 2 positives; drift after META/GOOGL enter the sample is expected. Fixture `bundle_kind=fixture` F1 must never be marketed as model quality. See [`TRAINING_DATA.md`](./TRAINING_DATA.md).

## JH-63.1 precision-weighted threshold (Mac A/B — 2026-09-24)

Same frozen parquet `data/derived/training_events.parquet`; `dataset_hash=a8bdd0fbda9ce31bce28de41a66a9698baeafb3fb58b1ab8ebdc586e1b10af1c`. Kaggle/FinBERT were **not** regenerated. Threshold fitting never used the held-out test. Comparison artifact (local): `artifacts/runs/jh63_threshold_compare_20260924T182930Z.json`.

| Method | t | Split | Precision | Recall | F1 | Confusion (TP/FP/TN/FN) | Notes |
|--------|---|-------|-----------|--------|----|-------------------------|-------|
| `train_f1_max` (A) | 0.50 | Train | 0.590 | 0.838 | 0.693 | 62 / 43 / 283 / 12 | |
| `train_f1_max` (A) | 0.50 | Test | **0.05** | 0.333 | **0.087** | 1 / 19 / 78 / 2 | `n_positive_test=3` |
| `train_val_fbeta_0.5` (B) | 0.65 | Train | 0.846 | 0.446 | 0.584 | 33 / 6 / 320 / 41 | |
| `train_val_fbeta_0.5` (B) | 0.65 | Val (fit) | 0.167 | 0.400 | F1=0.235 / Fβ=0.189 | 2 / 10 / 65 / 3 | last 20% of train; not test |
| `train_val_fbeta_0.5` (B) | 0.65 | Test | **0.0** | 0.0 | **0.0** | 0 / 0 / 97 / 3 | `n_positive_test=3`; zero positives predicted |

- `threshold_experiment_aborted`: false (both).
- **Verdict (locked TEST for Fβ method B): Fail.** Test F1=0.0 ≤ ≈0.087 baseline; test precision=0.0 < 0.08. Soft not met. Do not claim an improvement. Higher t=0.65 wiped all test positives (and FPs). With n_positive_test=3 the holdout remains noisy/weak.
- **Shipped default:** `train_f1_max`. Fβ remains available for A/B only (`--threshold-fitting train_val_fbeta_0.5`).
- This is not a production risk model; the gate is not alpha; there is no PnL.

## JH-63.2 MLOps experiment harness & run registry

The parallel experiment harness (`scripts/run_study.py`, `alphaguard study run/compare`) introduces declarative config matrices and an immutable run registry under `artifacts/runs/studies/<study_id>/`.

- **Harness Go ≠ Model Quality Go:** Passing harness tests proves that parallel execution, artifact isolation, and leakage guards function cleanly without cross-talk. It is not an assertion of trading edge or production readiness.
- **Fail Stays Fail:** The JH-63.1 Fail remains published and documented as evidence of rigorous point-in-time discipline. Shipped defaults are not altered without statistical power ($\ge 30$ locked-test positives via JH-63.3).
- **Leakage Guards:** HPO, threshold fitting, and calibration operate strictly on train/val splits; locked held-out test splits are evaluated once at the finish.
- See [`EXPERIMENTS.md`](./EXPERIMENTS.md).

## Pointers

- Product status / MV boxes → [`VISION.md`](./VISION.md)
- Contracts / as-of / gate policy → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Operator clone path → [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
- Skim storefront + category framing → [`../README.md`](../README.md) (claim depth lives here and in Deeper docs — README no longer has a Limitations section)
