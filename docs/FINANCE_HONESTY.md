# What AlphaGuard claims

AlphaGuard is a research lab for how AI trade ideas and risk controls work together, not a brokerage or PnL product.

## Claims we make

- **LLM analyst + code-owned risk veto:** the LLM analyst proposes BUY, HOLD or PASS. A code-owned downside-risk score and a fixed policy table decide whether a BUY may pass, so the LLM never approves its own idea. Trained bundles Platt-calibrate the veto's score on a train-internal validation slice; the committed demo bundle is calibrated on synthetic data.
- **Point-in-time discipline that tests for leakage:** features stop at `feature_as_of` (the last completed NYSE session), and retrieval keeps only hits with `available_at <= published_at` (`tests/test_asof.py`). A test changes every later price and checks that no feature moves (`tests/test_option_b_features.py`). The harness's own audit caught label windows crossing split boundaries; a trading-day purge in the study harness now removes them, with tests ([`EXPERIMENTS.md`](./EXPERIMENTS.md) §7).
- **Evaluation harness:** parallel study matrices (`alphaguard study`), floors fixed before each run, dataset-hash checks that fail closed, write-once run records with git SHA and config hash, and shortlist ranking on out-of-sample validation scores so the locked test is read only by the floor check. A multi-seed gate proposes candidates; a person makes the promotion call ([`PROMOTION_POLICY.md`](./PROMOTION_POLICY.md)).
- **Complete local pipeline:** replay-first smoke, Compose Kafka + Qdrant ingest, the risk-model training pipeline, an RSS polling CLI and fail-open LangSmith / Phoenix tracing. The smoke and unit tests run in CI; Kafka integration runs locally behind a flag.

## Scope

| Topic | Boundary |
|-------|---------|
| Veto, not alpha | Approve/reject is a risk control on proposed exposure; it makes no claim that an idea is profitable. |
| Costs / PnL | Out of scope: AlphaGuard is a risk-veto lab, not an execution algorithm, and publishes no backtest PnL or Sharpe figures. |
| Risk model | A research training pipeline on an 8,907-event freeze. The default smoke path uses the synthetic `bundle_kind=fixture` bundle. |
| Operations | Local and CI; the Yahoo RSS path is subject to external rate limits. |

## Pointers

- Product direction → [`VISION.md`](./VISION.md)
- Contracts / as-of / gate policy → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Operator clone path → [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
- Overview → [`../README.md`](../README.md)
