# AGENTS.md

AlphaGuard is a news-to-decision pipeline: an LLM analyst (LangGraph + Ollama) proposes BUY, HOLD or PASS, and a code-owned risk veto (calibrated XGBoost score + policy table) can reject a BUY. An offline harness tests whether the risk model clears floors fixed in advance.

## Commands

```bash
uv sync                                    # slim install; add --extra embed (Qdrant embeddings) or --extra train (FinBERT) when needed
brew install libomp                        # macOS, once: XGBoost needs OpenMP
uv run ruff check .                        # lint
uv run pytest -q                           # default suite: no keys, Docker or model download
uv run pytest -q tests/test_gate.py -k deterministic   # one test
make smoke-fixture                         # end to end with the fixture analyst (what CI runs)
make smoke                                 # end to end with host Ollama (OLLAMA_MODEL, default gemma4:e2b)
docker compose up -d && ALPHAGUARD_RUN_KAFKA_TESTS=1 uv run pytest -m kafka_integration
```

## Done means

- Lint, tests and `make smoke-fixture` pass locally, and CI is green.
- A bug fix ships with a test that fails on the old code; the commit message shows both runs.
- A contract change in `src/alphaguard/contracts/` updates `docs/ARCHITECTURE.md` §7 in the same PR.
- An experiment starts from a written plan with floors and stop rules, fixed before the run. Its record carries the dataset hash and git SHA.
- Run records in `runs/` stay as written; a correction is a new dated note beside them.

## Rules the tests guard

- Actions are BUY, HOLD or PASS (`contracts/proposals.py`).
- `PipelineService` is the one orchestrator. It stamps `event_id` and `ticker` from the input event.
- Retrieval keeps hits with `available_at <= published_at` and never returns the event itself. Features use the last completed NYSE session (`feature_as_of`).
- The label is `fwd_return_5d < -0.03`. Volatility enters as a feature or as the optional BUY veto.
- Thresholds, calibration and shortlist ranking use train and validation splits. Validation scores come from a booster trained only on the rows before the validation slice, and a one-class slice fails the run. The locked test is scored once per run, at the end, and read only by the floor check.
- The gate loads a bundle only when its manifest and feature names match.
- Run records are write-once; a rerun takes a new run or study id.

## Conventions

- Keep modules under 400 lines, split by responsibility. `train_option_b.py`, `study_walkforward.py` and `study_executor.py` are over; split one when you next change it.
- Write repo-relative paths in docs, plans and run summaries, and label claims Verified, Unverified or Unknown.
- Update a doc in place when its facts change, and link to it instead of copying numbers.
- Secrets live in `.env`, copied from `.env.example`.

## Read when

- Changing a contract, the gate policy or an as-of rule: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Running or reporting an experiment: [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`docs/PROMOTION_POLICY.md`](docs/PROMOTION_POLICY.md)
- Rebuilding training data: [`docs/TRAINING_DATA.md`](docs/TRAINING_DATA.md)
- Writing a public claim about results: [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md)
