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

## JH-63.1 lab note — train-val Fβ threshold (2026-09-24)

**Method (train-only):** freeze the time-ordered 100-row test; train the booster as today; choose `t` on the last 20% of **train** by maximizing Fβ with β=0.5 (tie-break: higher precision, then lower `t`). Control remains `threshold_fitting=train_f1_max` on full-train probs. Same booster, same frozen test. Artifact: [`lab/jh63_threshold_compare.json`](./lab/jh63_threshold_compare.json).

**Pins:** `builder_version=0.1.1`, seed 42, n=500, aliases on, FinBERT on. Ingest matched the 2026-07-21 rebuild (raw=1,400,469 → universe=10,215 → dedup=8,907 → sample=500; AAPL 67 / AMZN 67 / GOOGL 86 / META 71 / NVDA 100 / QQQ 109). `dataset_hash=6e900d503663d0858b6d5075f3f53443a0d0ce3afa46c9b740a4e2268a99591f`. `n_positive_test=3` (unchanged). Retrain used current host libraries (xgboost 3.3 / current yfinance adjustments) — **not** a byte-identical replay of the July bundle.

| Method | Split | n | F1 | Precision | Recall | Confusion (TP/FP/TN/FN) | t |
|--------|-------|---|----|-----------|--------|-------------------------|---|
| Published July 2026 (`train_f1_max`) | Test | 100 | ≈0.087 | 0.05 | ≈0.333 | 1 / 19 / 78 / 2 | — |
| Same-run `train_f1_max` | Train | 400 | ≈0.680 | ≈0.658 | ≈0.703 | 52 / 27 / 299 / 22 | 0.55 |
| Same-run `train_f1_max` | Test | 100 | **0.000** | 0.00 | 0.000 | 0 / 1 / 96 / 3 | 0.55 |
| Same-run `train_val_fbeta_0.5` | Train | 400 | ≈0.609 | ≈0.854 | ≈0.473 | 35 / 6 / 320 / 39 | 0.65 |
| Same-run `train_val_fbeta_0.5` | Val (last 20% of train) | 80 | ≈0.750 | 1.00 | 0.600 | 3 / 0 / 75 / 2 | 0.65 |
| Same-run `train_val_fbeta_0.5` | Test | 100 | **0.000** | 0.00 | 0.000 | 0 / 0 / 97 / 3 | 0.65 |

**Acceptance (plan):** PASS if locked-test precision ≥ 0.15 and F1 ≥ 0.20; SOFT PASS if FP ≤ 8 and F1 ≥ 0.12; FAIL if F1 ≤ 0.087 or precision < 0.08.

**Verdict: FAIL.** Candidate locked-test F1 = 0.000 and precision = 0.00. Fβ raised `t` 0.55 → 0.65 and cut the last false alarm (FP 1 → 0) but TP stayed 0 on `n_pos=3`. Default Option B threshold method remains `train_f1_max`. Do **not** claim an F1 improvement. Do **not** put these numbers on the README hero. Next lever is more positives / a new frozen split (JH-63.2), not peeking at this test to retune `t`.

## Pointers

- Product status / MV boxes → [`VISION.md`](./VISION.md)
- Contracts / as-of / gate policy → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Operator clone path → [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
- Skim storefront + category framing → [`../README.md`](../README.md) (claim depth lives here and in Deeper docs — README no longer has a Limitations section)
