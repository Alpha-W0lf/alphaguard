# Getting started — AlphaGuard (clean clone)

Clone-depth operator path for the **replay-first vertical slice**. For contracts see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); for interview gotchas see [`INTERVIEW.md`](INTERVIEW.md); skim + diagram in [`README.md`](README.md).

This is **not** “v1 complete.” Option B training is out of scope here; Kafka thin integration (Guide 04) is optional for smoke.

**Why packaging before Kafka (ARCHITECTURE §15 soft override):** interview ROI prioritizes a defendable FAQ + clone path + local-envelope evidence around the green vertical slice. Contracts unchanged.

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

Successful smoke writes a local run summary under **`artifacts/runs/<run_id>.json`** (gitignored). That file is the **mandatory LLMOps baseline**. Envelope fields `obs.langsmith` / `obs.phoenix` are status stubs until a real obs guide — local envelope fulfills packaging until H2 is reversed.

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

## Optional: Kafka + Qdrant integration (Guide 04)

```bash
docker compose up -d
# wait for kafka + qdrant healthy
export ALPHAGUARD_MODE=live ALPHAGUARD_RAG_MODE=qdrant
uv run alphaguard kafka consume
# other terminal:
uv run alphaguard kafka produce --event-id evt-aapl-001
# or: curl -X POST localhost:8000/trigger -H 'Content-Type: application/json' -d '...'
```

Default smoke path remains Kafka-down (`make smoke`). Integration tests: `ALPHAGUARD_RUN_KAFKA_TESTS=1 uv run pytest -m kafka_integration`.

Do **not** tick VISION MV packaging boxes from this file — Align-docs owns checkbox updates after Review evidence.
