# AlphaGuard: vision

**Purpose:** a public reference pipeline for how an AI analyst and a code-owned risk control work together: news → retrieval → structured trade idea → downside-risk veto, runnable locally end to end.

**Owner:** Thomas Chacko. Binding contracts, as-of rules and gate policy live in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## The problem

Financial news arrives as an unstructured firehose. Teams need a credible, explainable path from headline to retrieved context to a structured proposal to a risk decision. Most demos stop at a chat wrapper; a real system needs streaming, as-of discipline, typed agent contracts, observability and tabular ML in one place that can be cloned and inspected.

## What it does

- **Ingest (Compose path):** headlines flow through Kafka; consumers embed and upsert into Qdrant as a rolling context window. The default smoke path replays fixtures.
- **LLM analyst:** LangGraph on a local Ollama model reads as-of-filtered context and returns schema-checked JSON (`BUY`, `HOLD` or `PASS`).
- **Risk veto (the architecture under test):** a calibrated XGBoost downside-risk score and a deterministic policy map `(action, score)` to approve or reject. The harness decides whether a risk model is good enough to drive it; none has cleared the floors fixed in advance so far.
- **Observability:** every run writes a local run record; LangSmith and Phoenix receive traces when configured.
- **Evaluation harness:** parallel study matrices with floors fixed before each run, write-once records and a multi-seed promotion gate.

AlphaGuard is a research lab: it manages no capital and connects to no brokerage.

## Design principles

1. **The analyst is not the risk model.** The LLM proposes; code-owned scoring and policy decide.
2. **Point-in-time by construction.** Features use completed sessions before the headline, retrieval keeps only earlier context, and tests check both. The harness also tests for leakage across splits; its own audit caught a label-window leak, and a trading-day purge now guards the study harness's splits.
3. **Hybrid AI + ML.** Agentic orchestration for the proposal, supervised tabular ML for the risk score.
4. **Measured before promoted.** Thresholds, calibration and selection use train and validation data; the locked test is read once per run by the floor check, and a person makes the promotion call.
5. **No secrets or proprietary trading logic.** No keys in git and no proprietary trading logic in this repo.
6. **AI-native build, human-validated ship.** Specs and tests first; agents work from [`AGENTS.md`](../AGENTS.md).

## Direction

- A live feature builder so brand-new headlines can be scored end to end.
- An analyst evaluation set (schema pass rate, grounding, prompt-injection cases) gated in CI.
- New risk-model studies, each starting from a written plan with its floors.

See [`EXPERIMENTS.md`](./EXPERIMENTS.md), [`TRAINING_DATA.md`](./TRAINING_DATA.md) and [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md).
