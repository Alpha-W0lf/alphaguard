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

## Pointers

- Product status / MV boxes → [`VISION.md`](./VISION.md)
- Contracts / as-of / gate policy → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Operator clone path → [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
- Skim + Limitations → [`../README.md`](../README.md)
