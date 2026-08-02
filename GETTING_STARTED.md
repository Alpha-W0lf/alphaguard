# Getting started — AlphaGuard (clean clone)

Replay-first smoke path for the news → RAG → BUY/HOLD/PASS → downside-risk gate demo.

- Skim + diagram: [`README.md`](README.md)
- Contracts: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Finance claims: [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md)
- Technical FAQ: [`INTERVIEW.md`](INTERVIEW.md)

**Status:** Bounded local demo is runnable; production hardening and deeper live evaluation are incomplete. Finish line = **local + CI** (not hosted). Default smoke stays Kafka-down with fixtures. **License:** PolyForm Noncommercial 1.0.0 — source-available / non-commercial (not OSI open source; not MIT); commercial use → contact copyright holder. See [`LICENSE`](LICENSE).

---

## Prerequisites

- **Python 3.12** (see `.python-version`) via [`uv`](https://github.com/astral-sh/uv)
- Host **Ollama** with default model `gemma4:e2b` (or documented fallback)
- macOS XGBoost: `brew install libomp` (smoke sets `KMP_DUPLICATE_LIB_OK=TRUE`)

---

## Clean-clone path

From repo root:

```bash
# 1. Sync (Python 3.12 from .python-version)
uv sync --all-extras
# or: make sync

# 2. Env template (never commit .env)
cp -n .env.example .env

# 3. Pull default generator (D1)
ollama pull gemma4:e2b
# If pull returns HTTP 412: upgrade Ollama, then pull again.
# Fallback: export OLLAMA_MODEL=qwen3.5:4b && ollama pull qwen3.5:4b

# 4. Fixture model bundle (plumbing only — not Option B)
make bundle

# 5. Smoke with Kafka DOWN (Makefile: "Kafka must remain stopped")
make smoke
```

Smoke defaults: `ALPHAGUARD_MODE=replay`, `ALPHAGUARD_RAG_MODE=fixture`, `resource_mode=replay_fixture`. **Compose is optional** — smoke does not require Kafka or Qdrant.

### Preflight

```bash
make preflight
```

Checks replay-mode readiness (Ollama reachability / model tags per config). If the **primary** model tag is missing, preflight may soft-fall back to `OLLAMA_FALLBACK_MODEL` (`qwen3.5:4b`) — treat that as warning-debt, not “gemma proven.”

### Where the envelope lands

Successful smoke writes a local run summary under **`artifacts/runs/<run_id>.json`** (gitignored). That file is the **mandatory LLMOps baseline**. With default env, `obs.langsmith=skipped` and `obs.phoenix=skipped` (smoke never needs a LangSmith key or Phoenix collector). When `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` are set, a real LangSmith Client run may appear and `extras.langsmith_run_id` may be set. When `PHOENIX_ENABLED=true`, a real Phoenix/OTEL chain span may appear and `extras.phoenix_span_id` may be set. Do not invent LangSmith/Phoenix UI screenshots.

### macOS `libomp`

```bash
brew install libomp
```

`make smoke` already exports `KMP_DUPLICATE_LIB_OK=TRUE` and `OMP_NUM_THREADS=1`.

---

## Defaults & honesty

| Topic | Truth |
|-------|--------|
| Default RAG | `ALPHAGUARD_RAG_MODE=fixture` |
| Kafka / Qdrant | Optional; smoke does **not** need `docker compose up` |
| `bundle_kind=fixture` | Plumbing only — do not cite synthetic F1 as model quality |
| Primary model missing | Preflight may use fallback; document which model actually ran |

## Optional: Kafka + Qdrant integration

```bash
docker compose up -d
# wait for kafka + qdrant healthy
export ALPHAGUARD_MODE=live ALPHAGUARD_RAG_MODE=qdrant
uv run alphaguard kafka consume
# other terminal:
uv run alphaguard kafka produce --event-id evt-aapl-001
# or: curl -X POST localhost:8000/trigger -H 'Content-Type: application/json' -d '...'
```

### Optional: Yahoo RSS poll

Requires Compose Kafka + a running consumer (same as above). **Not** required for smoke.

```bash
uv run alphaguard rss poll --ticker AAPL --max-items 10
# demo loop only (not a production daemon):
# uv run alphaguard rss poll --ticker AAPL --loop --interval-sec 120
```

Yahoo may flake or block; offline fixtures under `data/fixtures/rss/` are CI truth. Default smoke path remains Kafka-down (`make smoke`). Integration tests: `ALPHAGUARD_RUN_KAFKA_TESTS=1 uv run pytest -m kafka_integration`. Optional live RSS probe: `ALPHAGUARD_RUN_RSS_LIVE=1 uv run pytest -m rss_live`.

More: Technical FAQ ([`INTERVIEW.md`](INTERVIEW.md)) · Architecture · Finance honesty.
