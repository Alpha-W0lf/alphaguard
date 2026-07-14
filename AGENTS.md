# Agent guidance — AlphaGuard

**Vertical slice only** (guide 01). Not “v1 complete.”

## Locked stack (do not reopen)

- Python 3.11+ / `<3.14` (`uv`), LangGraph + host **Ollama** (`OLLAMA_MODEL` default `gemma4:e2b`, fallback `qwen3.5:4b`)
- **`gemma4:e2b`:** default generator; needs a current Ollama (`pull` can 412 on older builds). If primary tag missing, preflight may use `qwen3.5:4b` (documented D1 fallback). Do not claim gemma works without a successful pull / smoke.
- Compose Kafka + Qdrant (smoke does **not** require Kafka; default smoke = `ALPHAGUARD_RAG_MODE=fixture`)
- Agent 2 = XGBoost **downside-risk scorer** + deterministic policy
- LLMOps: local run summary **mandatory**; LangSmith/Phoenix best-effort fail-open
- FinBERT = offline batch only (never during smoke)

## AG1–AG3 (one-liners)

- **AG1:** Actions `BUY|HOLD|PASS` only (`SELL` reject). Gate maps `(action, downside_risk_score[, vol veto]) → approve|reject`.
- **AG2:** Learned label = forward downside return only — never OR volatility into the label.
- **AG3:** Unified as-of UTC; every hit has `available_at <= published_at`; features carry `feature_as_of`.

## Engineering rails

- Prefer ≤300 lines/file (hard max 400). Top-level modules only: `contracts/`, `ingest/`, `pipeline/`, `rag/`, `agents/`, `ml/`, `infra/`, `api/`, `obs/`, `eval/`.
- **Replay-first:** `ALPHAGUARD_MODE=replay` bypasses live Kafka.
- Secrets only via `.env` from `.env.example` — never commit keys.
- No brokerage APIs, no Lowd Capital, no neural reranker, no second LLM auditor.

## Docs SSOT

- Product / why → [`docs/VISION.md`](docs/VISION.md)
- Contracts / how → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
