# Finance honesty — what AlphaGuard claims (and does not)

**Audience:** Quantitative risk, ML engineering, and systems research readers evaluating architecture, temporal rigor, and empirical honesty.  
**Scope:** Architectural and experiment honesty. Not a production risk model. Not a brokerage, execution engine, or PnL strategy.

## Claims we make

- **Engineered multi-agent separation of concerns:** LLM idea generation (Agent 1) is decoupled from an auditable, code-owned tabular risk veto gate (Agent 2), preventing hallucinated approvals.
- **Strict look-ahead and point-in-time discipline:** Binding temporal invariants guarantee zero future information leakage. Engineered features terminate at `feature_as_of` (exchange calendar session closes); retrieval contexts enforce `available_at <= published_at`. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) §8 and `tests/test_asof.py`.
- **Empirical MLOps rigor & reproducible experimentation:** Parallel study matrices (`alphaguard study`), config-driven execution, artifact isolation, and immutable run registries evaluate candidates on locked held-out test splits.
- **Fail stays Fail:** Negative results are published directly as hard empirical evidence of statistical discipline rather than hidden or reframed.
- **Bounded reference pipeline complete:** Guides 01–08 deliver a self-contained local + CI system: replay-first smoke, Compose Kafka + Qdrant streaming integration, Option B tabular training pipeline, live RSS polling CLI, and fail-open telemetry adapters (LangSmith / Phoenix).

## Claims we do **not** make

| Topic | Honesty |
|-------|---------|
<<<<<<< HEAD
| Gate ≠ alpha | Approve/reject is a **risk veto**, not a signal that the idea is profitable. |
| Costs / slippage / PnL | **Omitted on purpose** — this is a veto gate lab, not an execution strategy. Do not invent backtest PnL claims. |
| Production risk model | Lab-scale Option B train (JH-63.1 freeze n=500; JH-63.3 full-pool freeze n=8907). Default smoke uses `bundle_kind=fixture` plumbing only. Not a production risk model. |
| Live eval completeness | No required live-Ollama numeric schema-pass rates; Yahoo RSS may flake; not 24/7 SRE. |
=======
| Gate ≠ alpha | Approve/reject is an asymmetric **risk veto** on proposed exposure, not a predictive signal that an idea is profitable. We claim zero alpha. |
| Costs / slippage / PnL | **Omitted on purpose** — AlphaGuard is a risk veto lab, not an execution algorithm. We publish zero backtest PnL or Sharpe claims. |
| Production risk model | Option B is an empirical **lab training pipeline** on ~500 events; the default smoke path uses synthetic `bundle_kind=fixture` plumbing to prove orchestration. |
| Live eval completeness | No inflated live-Ollama numeric schema-pass rates; Yahoo RSS is subject to external rate limits; not 24/7 production SRE. |
>>>>>>> c2e5af1 (docs(voice): implement JH-63.4 voice pass for technical mastery and empirical honesty)

## Option B lab metrics (local manifest — regenerate may differ)

Quoted from a local `data/derived/model_bundle_option_b/manifest.json` (`bundle_kind=option_b`, created `2026-07-21T20:50:31Z` after archive-alias rebuild). **Not committed**; retrain locally via `scripts/train_option_b_gate.py`. Honest zero and weak holdout results are expected at this sample scale and are published verbatim rather than hidden.

| Split | n | F1 | Precision | Recall | Confusion (TP/FP/TN/FN) |
|-------|---|----|-----------|--------|-------------------------|
| Train | 400 | ≈0.693 | ≈0.590 | ≈0.838 | 62 / 43 / 283 / 12 |
| Test | 100 | **≈0.087** | 0.05 | ≈0.333 | 1 / 19 / 78 / 2 |

Notes: `n_positive_test=3` — test F1 reflects high rare-class variance at $n=100$, not masked performance. Prior pre-alias manifest (2026-07-17) had test F1 = 0.0 on 2 positives; drift after META/GOOGL enter the sample demonstrates real dataset sensitivity. Fixture `bundle_kind=fixture` F1 must never be marketed as model quality. See [`TRAINING_DATA.md`](./TRAINING_DATA.md).

## JH-63.1 precision-weighted threshold (Mac A/B — 2026-09-24)

Same frozen parquet `data/derived/training_events.parquet`; `dataset_hash=a8bdd0fbda9ce31bce28de41a66a9698baeafb3fb58b1ab8ebdc586e1b10af1c`. Kaggle/FinBERT were **not** regenerated. Threshold fitting never touched the locked held-out test split. Comparison artifact (local): `artifacts/runs/jh63_threshold_compare_20260924T182930Z.json`.

| Method | t | Split | Precision | Recall | F1 | Confusion (TP/FP/TN/FN) | Notes |
|--------|---|-------|-----------|--------|----|-------------------------|-------|
| `train_f1_max` (A) | 0.50 | Train | 0.590 | 0.838 | 0.693 | 62 / 43 / 283 / 12 | Shipped baseline |
| `train_f1_max` (A) | 0.50 | Test | **0.05** | 0.333 | **0.087** | 1 / 19 / 78 / 2 | `n_positive_test=3` |
| `train_val_fbeta_0.5` (B) | 0.65 | Train | 0.846 | 0.446 | 0.584 | 33 / 6 / 320 / 41 | |
| `train_val_fbeta_0.5` (B) | 0.65 | Val (fit) | 0.167 | 0.400 | F1=0.235 / Fβ=0.189 | 2 / 10 / 65 / 3 | last 20% of train; not test |
| `train_val_fbeta_0.5` (B) | 0.65 | Test | **0.0** | 0.0 | **0.0** | 0 / 0 / 97 / 3 | `n_positive_test=3`; zero positives predicted |

- `threshold_experiment_aborted`: false (both).
- **Verdict (locked TEST for Fβ method B): Fail.** Test F1=0.0 ≤ ≈0.087 baseline; test precision=0.0 < 0.08. Threshold tuning on rare-class regimes without sufficient support is noise: shifting threshold to $t=0.65$ eliminated false positives at the cost of eliminating all true positive coverage. We do not apologize for this Fail or soften it: documenting genuine negative results on held-out test data is fundamental engineering rigor.
- **Shipped default:** `train_f1_max`. Fβ remains available for A/B benchmarking (`--threshold-fitting train_val_fbeta_0.5`).
- **Trading boundary:** This is a downside-risk veto lab, not a production risk model; the gate is not alpha; there is no PnL.

## JH-63.2 MLOps experiment harness & run registry

The parallel experiment harness (`scripts/run_study.py`, `alphaguard study run/compare`) introduces declarative config matrices and an immutable run registry under `artifacts/runs/studies/<study_id>/`.

- **Harness Go ≠ Model Quality Go:** Passing harness test suites proves that parallel worker execution, artifact isolation, and leakage guards function cleanly without cross-talk. It is an infrastructure milestone, not an assertion of trading edge or production readiness.
- **Fail Stays Fail:** The JH-63.1 Fail remains published and documented as evidence of rigorous point-in-time discipline. Shipped model defaults are not altered without statistical power ($\ge 30$ locked-test positives).
- **Leakage Guards:** Hyperparameter optimization, threshold fitting, and probability calibration operate strictly on train/val splits; locked held-out test splits are evaluated exactly once at study completion.
- See [`EXPERIMENTS.md`](./EXPERIMENTS.md).

## JH-AG-93.1 auto multi-seed promotion gate

An automated multi-seed gate in the harness (`study_promotion.py`) tests shortlisted configurations against extra seeds (`[7, 123]`) and evaluates locked floors ($F_1 \ge 0.30$, $P \ge 0.25$, $\text{AUPRC} \ge 0.18$).

- **Harness Candidate ≠ Model Quality Go:** The automated harness output (`promotion_decision: candidate`) only indicates that variance across required seeds cleared minimum statistical floors. It proposes a candidate; only a human review can claim **Model Quality Go**.
- **Model Quality Go Remains UNCLAIMED:** Historical multi-seed evaluations failed precision floors ($P = 0.1711$ on seed 7, $P = 0.2263$ on seed 123). Fail remains published.
- **Shipped Default Remains `train_f1_max`:** No threshold method change is made without human approval and full documentation.
- **No PnL / Market Claims:** AlphaGuard is a downside-risk veto lab, not an execution or trading strategy.
- See [`PROMOTION_POLICY.md`](./PROMOTION_POLICY.md).

## JH-63.3 full-pool re-baseline (`train_f1_max` — 2026-09-24)

**New freeze**, not a retrofit of the JH-63.1 Fail. Canonical parquet expanded to the full local dedup pool (8,907 deduped events across `AAPL, AMZN, GOOGL, META, NVDA, QQQ`); label unchanged `fwd_return_5d < -0.03`. JH-63.1 Fail on the tiny freeze (`a8bdd0fb…`, n_positive_test=3, test F1≈0.087) **remains published**.

| Field | Value |
|-------|-------|
| Rows | **8907** (train 7125 / locked test 1782) |
| `n_positive_test` | **233** (Phase-1 ≥30 / stretch ≥50 met) |
| `dataset_hash` | `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3` |
| Threshold method | `train_f1_max` (shipped default; t=0.50; never fit on test) |
| git SHA | `7974716` (main / JH-63.2 harness) |
| config_hash | `940e7aa8ab69f0c3` |
| Wall clock | ≈3.0 s on M2 Pro (CPU) |
| Bundle (local) | `data/derived/model_bundle_option_b_jh633_f1max/` |
| Run JSON | `artifacts/runs/option_b_train_20260924T192606Z.json` |
| Registry | `artifacts/runs/studies/single_runs/runs/option_b_20260924T192606Z.json` |
| JH-63.1 backup | `data/derived/training_events_jh631_a8bdd0fb.parquet` retained |

| Split | n | n_pos | Precision | Recall | F1 | Fβ(β=0.5) | AUPRC | Brier | Confusion (TP/FP/TN/FN) |
|-------|---|------:|----------:|-------:|---:|----------:|------:|------:|-------------------------|
| Train | 7125 | 1273 | 0.4625 | 0.7651 | 0.5765 | 0.5022 | 0.6521 | 0.1635 | 974 / 1132 / 4720 / 299 |
| Locked test | 1782 | **233** | **0.1280** | **0.5966** | **0.2108** | **0.1518** | **0.1442** | **0.3055** | **139 / 947 / 602 / 94** |

- **Frame:** new baseline on expanded freeze with genuine statistical power. Do **not** claim “JH-63.1 Fail fixed.” Different sample + different time cut.
- **Harness Go ≠ Model Quality Go.** This records an honest empirical lab baseline; it is **not** a Model Quality Go / promotion decision.
- **Shipped default remains `train_f1_max`.** No Fβ default switch from this run (no A/B in this step). CLI default in `scripts/train_option_b_gate.py` aligns with this shipped default.
- Train/test F1 gap ≈0.366 — overfit warning expected at lab scale; holdout still weak relative to train (high FP count).
- This is not a production risk model; the gate is not alpha; there is no PnL.
- See [`TRAINING_DATA.md`](./TRAINING_DATA.md) and [`EXPERIMENTS.md`](./EXPERIMENTS.md).

## Pointers

- Product status / MV boxes → [`VISION.md`](./VISION.md)
- Contracts / as-of / gate policy → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Operator clone path → [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
- Skim storefront + category framing → [`../README.md`](../README.md) (claim depth lives here and in Deeper docs — README no longer has a Limitations section)
