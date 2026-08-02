# Agent guidance — AlphaGuard

**Bounded minimum viable build complete** (guides 01–04 + **05a** dataset builder + **05b** Option B XGBoost train + **06** thin live RSS poll + **07** LangSmith real fail-open spans + **08** Phoenix real fail-open spans); **production hardening and deeper live evaluation incomplete.** Finish line = **local + CI** (not hosted). Still **not** a production risk model / **not** interview-fluency proven. Walkthrough + daily hand-coding = **Interview prep** in `docs/VISION.md` (not build blockers). Finance honesty: [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md). Guide 02 interview packaging landed (`FAQ.md`, `GETTING_STARTED.md`, `docs/assets/`). Guide 03 eval harness landed — ≥21 executable goldens (not live-Ollama rates). Guide 04 Kafka + Qdrant thin integration landed (producer/consumer/`/trigger`/UUID5; default smoke still Kafka-down `replay_fixture`). Guide **05a** training-row builder + Guide **05b** `bundle_kind=option_b` train CLI landed — **default smoke still fixture**. Guide **06** Yahoo RSS → produce (`alphaguard rss poll`) — thin operator path; Yahoo may flake; **not** agent-on-consume / **not** 24/7 reliability. Guide **07** LangSmith Client emit when tracing+key. Guide **08** Phoenix OTEL chain span when `PHOENIX_ENABLED` — smoke never requires LangSmith key or Phoenix collector. Thin polish: ARCHITECTURE header through guides 01–08; minimal GitHub Actions `pytest` on `main`/PRs (no smoke/Ollama in CI). **License:** PolyForm Noncommercial 1.0.0 — source-available / non-commercial (not OSI open source; not MIT); see [`LICENSE`](LICENSE).

## Locked stack (do not reopen)

- Python 3.11+ / `<3.14` (`uv`), LangGraph + host **Ollama** (`OLLAMA_MODEL` default `gemma4:e2b`, fallback `qwen3.5:4b`)
- **`gemma4:e2b`:** default generator; needs a current Ollama (`pull` can 412 on older builds). If primary tag missing, preflight may use `qwen3.5:4b` (documented D1 fallback). Do not claim gemma works without a successful pull / smoke.
- Compose Kafka + Qdrant (smoke does **not** require Kafka; default smoke = `ALPHAGUARD_RAG_MODE=fixture`)
- Agent 2 = XGBoost **downside-risk scorer** + deterministic policy
- LLMOps: local run summary **mandatory**; LangSmith real fail-open spans when configured; Phoenix real fail-open spans when enabled; fail-open relative to gate
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
- Finance claims → [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md)
- License → [`LICENSE`](LICENSE) (PolyForm-NC 1.0.0 — source-available / non-commercial; not OSI open source / not MIT; commercial use → contact copyright holder)
