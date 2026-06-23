# AlphaGuard: Vision Document

**Purpose:** Build a bounded, public reference pipeline that teaches and demonstrates senior AI/data-engineering skills so Tom can pass technical interview rounds—not just recruiter screens.

**Status:** Planning

**Last Updated:** June 23, 2026

**Owner:** Tom

**Guide:** Structured per [`second_brain/docs/guides/meta_creating_vision_docs.md`](../../second_brain/docs/guides/meta_creating_vision_docs.md). Detailed architecture belongs in a separate doc; this file is the decision framework.

**Related project:** [Lowd Capital](../lowd_capital/docs/VISION.md) — private, real trading factory. AlphaGuard is intentionally separate; no proprietary alpha logic lives here.

---

## Problem Statement

### The Friction

Tom is a Senior AI Engineer (data engineering background) between contracts, targeting fully remote roles in the $180k–$240k base range. Recruiter screens are not the bottleneck. The bottleneck is **late-stage technical interviews**: live hand-coding, tool-specific deep dives, and system design under pressure—often without AI assistants.

Daily work is AI-native (Cursor, Copilot, Codex). That produces shippable systems quickly, but interview loops still test **manual fluency**: Python without autocomplete, Kafka consumer semantics, LangGraph state, RAG tradeoffs, and ML pipeline basics.

### Current Workarounds

- Personal projects exist but are not packaged as a **coherent, explainable, interview-ready artifact** aligned to 2026 hiring demand (agentic AI, streaming, vector DBs, LLMOps).
- Studying docs in isolation does not force the integration muscle memory that interviews probe.
- A serious trading platform ([Lowd Capital](../lowd_capital/docs/VISION.md)) must stay private; it cannot serve as a public portfolio piece.

### Why This Matters to Me

A W-2 remote offer unlocks a home purchase timeline ($250k–$300k) and stable income. Passing technical rounds requires **genuine familiarity** with the stack, not just a README that claims it. AlphaGuard is a **learning lab with a finish line**, not an open-ended portfolio.

### Frequency

Intensive build over **6–7 days max**. Interview prep (explain-without-AI drills) continues for weeks after ship.

---

## Solution Overview

### What It Does

**AlphaGuard** is a stateful multi-agent financial research pipeline that ingests news, retrieves context via RAG, proposes structured trade ideas (Agent 1), and gates them through a supervised ML risk classifier (Agent 2)—with full LangSmith tracing.

It simulates institutional “analyst + risk” separation using tools employers recognize in mid-2026: **Kafka, Qdrant, LangGraph, Ollama, LangSmith, FastAPI, XGBoost**.

### How I'll Use It

1. **Build** the pipeline locally on M2 Pro (16GB) with Docker Compose.
2. **Study** each component daily: hand-write core pieces without AI after implementing with AI.
3. **Share** public GitHub repo + LangSmith screenshots + short Loom walkthrough before technical rounds.
4. **Defend** architecture, tradeoffs, leakage controls, and failure modes in system design interviews.

### Key Capabilities

1. **Event-driven ingestion:** Financial headlines flow through Kafka; consumers embed and upsert into Qdrant (rolling context window).
2. **Agent 1 — LLM Analyst:** LangGraph + local Ollama (config-driven ~8B model; see Technical Approach) reads RAG context and outputs structured JSON (`action`, `ticker`, `confidence`, `rationale`) via Ollama structured outputs.
3. **Agent 2 — ML Risk Gate:** XGBoost classifier trained on **500 historical headline events** (Option B data strategy) approves or rejects Agent 1 proposals based on market-regime features—not Agent 1 backtest labels.
4. **LLMOps observability:** Every agent step traced in LangSmith (latency, tokens, trajectories).
5. **Interview artifacts:** README architecture diagram, `INTERVIEW.md` FAQ, optional replay demo of cached end-to-end runs.

### Workflow Integration

```
Study job posting → Map skills gap → Build/rehearse AlphaGuard component →
Send repo + Loom before technical round → Whiteboard same architecture live
```

AlphaGuard does **not** run in production, manage capital, or connect to live brokerage APIs.

---

## Design Principles

### 1. Finish Line Over Feature Count

**Rationale:** Scope creep kills weekend/week projects and delays interview prep.

**In Practice:** v1 is done when one headline flows end-to-end with LangSmith trace + ML gate + public README. No cloud Kafka deploy, no fine-tuning, no hybrid search, no second LLM agent.

### 2. Learn by Building, Prove by Explaining

**Rationale:** The repo gets the interview; **fluency** passes the interview.

**In Practice:** After each build day, 30–45 minutes without AI: explain one component aloud, hand-write a minimal version next morning. `INTERVIEW.md` documents tradeoffs and gotcha questions.

### 3. Hybrid AI + ML (Not LLM-Only)

**Rationale:** Senior AI/DE roles expect both agentic systems and tabular ML discipline.

**In Practice:** Agent 1 = LLM. Agent 2 = XGBoost on engineered features. README states clearly: Agent 2 is a **regime/risk gate**, not an alpha model.

### 4. Honest Data Science

**Rationale:** Interviewers will probe leakage, labels, and train/test methodology.

**In Practice:** 500 events, time-based split, features computed only from data available at headline time, labels from forward returns after event. Document limitations openly.

### 5. Public Shell, No Secret Sauce

**Rationale:** Protect [Lowd Capital](../lowd_capital/docs/VISION.md) proprietary logic.

**In Practice:** Public repo. No live keys in git. No strategies that overlap with private trading research.

### 6. AI-Native Build, Human-Validated Ship

**Rationale:** Tom builds with AI agents; quality comes from specs, tests, and review—not typing every line.

**In Practice:** Spec-first and test-first for ML gate JSON schema and feature pipeline. Repo-level agent guidance (`AGENTS.md`) enforces simplicity and file size limits.

---

## Success Criteria

### Minimum Viable (v1 Done)

- [ ] `docker compose up` runs Kafka + Qdrant locally
- [ ] 500 headline events dataset built (`data/training_events.parquet`) with documented schema
- [ ] XGBoost risk model trained with time-based holdout; metrics logged in README
- [ ] One live headline (or replayed sample) flows: ingest → RAG → Agent 1 → Agent 2 → LangSmith trace
- [ ] Public GitHub with architecture diagram, stack table, and limitations section
- [ ] `INTERVIEW.md` with 15+ gotcha Q&A
- [ ] Tom can give 10-minute unprompted architecture walkthrough without opening code
- [ ] Parallel interview prep: 15–30 min/day hand-coding (separate from build) while project runs

### Signs It's Working

- Technical interviewers engage on system design instead of doubting AI-only coding
- Tom can answer tool-deep questions (consumer groups, state schema, leakage) without reading docs
- Project ships in ≤7 days; no “one more feature” spiral

### Future Enhancements (Post-v1, Optional)

- Streamlit replay UI for cached runs
- Hold-out evaluation: Agent 1 on 50 headlines + Agent 2 block rate analysis
- Fine-tuned small sentiment model (only if v1 shipped early)

---

## Non-Goals

### Out of Scope for v1

- Live trading, paper brokerage, or real capital at risk
- Proprietary alpha research (belongs in Lowd Capital)
- Model fine-tuning or full MLOps platform (MLflow registry, K8s, Terraform)
- Cloud deployment of full Kafka stack
- Second adversarial LLM agent (Agent 2 is ML, not LLM)
- Cybersecurity / SOC log analysis theme
- Beating recruiter screens (already not the bottleneck)
- Training Agent 2 on historical Agent 1 outputs (Option C — deferred)

### Why These Are Non-Goals

Each item adds days of work without improving the core outcome: **technical interview fluency** on a credible, bounded system. Lowd Capital owns long-horizon trading ambition.

---

## Technical Approach

### Stack Summary

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | DE/AI ecosystem, interview familiarity |
| Streaming | Apache Kafka (Docker) | Enterprise data eng signal; interview topics |
| Vector DB | Qdrant | In-demand vs Chroma; payload filtering |
| Orchestration | LangGraph | Stateful multi-agent standard in 2026 |
| Local LLM | Ollama + config-driven model (see selection table) | Free; swappable without code changes |
| Embeddings | `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) | Local, fast; separate from agent LLM |
| LLMOps | LangSmith | Market leader for traces in AI eng interviews |
| API | FastAPI | Thin trigger/replay endpoint |
| ML Gate | XGBoost + scikit-learn | Fast local training; DE interview staple |
| Sentiment features | FinBERT inference (HF) | Financial domain signal without training |
| Prices | yfinance | Free OHLCV for features and labels |
| Packaging | Docker Compose | One-command local infra |

### Agent 2 Data Strategy (Option B — Locked for v1)

**Training corpus:** 500 headline events aligned to tickers and trading days.

**Per-event features (computed at headline time `t`):**
- FinBERT sentiment score
- `volatility_20d`, `return_5d_prior`, `return_20d_prior` for ticker
- `spy_return_5d` (market context)
- Optional: headline source bucket, word count

**Label (training only):**
- `HIGH_RISK = 1` if forward 5-trading-day return `< -3%` OR `volatility_20d` ≥ 90th percentile of training set
- `OK = 0` otherwise
- Drop ambiguous middle zone if needed to reduce noise

**Split:** Time-ordered 80/20 (no random shuffle).

**Inference:** Agent 1 JSON + live features → `approve` / `reject` + `risk_score`. LangSmith logs both.

**Headline sources (default):** Primary = curated CSV/Kaggle financial news archive for historical 500; live demo = RSS (Yahoo Finance). Document exact dataset in README.

**Ticker universe (default):** AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ (8 tickers).

### Local LLM Selection (Config-Driven, Not Hardcoded)

Early brainstorming cited `llama3` 8B as a safe default. For v1 on a **16GB M2 Pro**, prefer a **2026-era model** that fits alongside Docker (Kafka, Qdrant) and produces reliable structured JSON via Ollama's `format` + JSON schema.

**Important:** The **Qwen 3.6** family exists on Ollama (`qwen3.6:27b`, `qwen3.6:35b`) but there is **no official Qwen 3.6 8B dense model**. Qwen 3.6 sizes are primarily **27B dense** and **35B-A3B MoE** (~24GB quantized)—too large to run concurrently with full Docker stack on 16GB. For AlphaGuard v1, treat Qwen 3.6 as a **future upgrade path** on 32GB+ hardware or when Ollama is the only heavy service running—not the default for this machine.

**Selection criteria (16GB M2 Pro):**
- Quantized load roughly **5–10GB** with headroom for OS + containers
- Ollama **structured outputs** (`format` + JSON schema) for Agent 1
- Swappable via config (`OLLAMA_MODEL`); never hardcoded in agent logic

**Recommended candidates (benchmark one at implementation):**

| Priority | Ollama tag | Approx. size | Why consider |
|----------|------------|--------------|--------------|
| 1 | `qwen3.5:9b` | ~6GB | Workspace-validated; good quality/speed on Apple Silicon |
| 2 | `qwen3:8b` | ~5GB | Fast, proven on 16GB Macs |
| 3 | `gemma4:latest` / `gemma4:e4b` | ~9–10GB | Agent-oriented; native tool/JSON calling |
| 4 | `qwen3.5:4b` | ~3GB | If RAM is tight after Docker is up |

**Future / not v1 default on 16GB:**

| Model | Notes |
|-------|--------|
| `qwen3.6:35b` | MoE; ~24GB—fits 32GB M2 Max with care, not 16GB + Docker |
| `qwen3.6:27b` | ~17GB dense—marginal on 16GB alone |
| `llama3.1:8b` | Legacy fallback only |

**Cross-reference:** `second_brain/docs/guides/best_practices_local_llm.md`, `best_practices_ollama_thinking_models.md`, and `simple_content_platform` model registry research for M2 Max vs M2 Pro constraints.

**Interview story:** *"Agent LLM is config-driven. We benchmarked [model] for structured JSON on 16GB hardware with structured outputs—not model hype."*

### Key Patterns

- **Brains never call exchange APIs** — no execution layer in v1
- **Structured JSON contracts** between agents with schema validation
- **Separation of concerns:** `ingest/`, `agents/`, `ml/`, `infra/` modules

### Automation

- Manual CLI / FastAPI trigger for demos
- No 24/7 daemon required for v1

### Sharing Strategy

| Artifact | Purpose |
|----------|---------|
| Public GitHub (pinned) | Primary proof |
| LangSmith trace screenshots | LLMOps proof |
| 3–5 min Loom | For HMs/interviewers who won't clone repo |
| `INTERVIEW.md` | Deep-dive prep + send before technical round |

No full cloud deploy required for v1.

---

## Implementation Risks (Vision-Level)

| Risk | Why it matters | Mitigation |
|------|----------------|------------|
| **16GB RAM contention** | Kafka + Qdrant + Ollama + FinBERT together can swap-thrash | Run services sequentially during dev; limit concurrent containers; pick smallest viable LLM quant |
| **500-event dataset quality** | Bad alignment → weak ML gate → embarrassing interview story | Document schema; manual spot-check 20 rows; time-based split only |
| **Look-ahead leakage** | Features accidentally use future prices | Architecture doc defines strict `as-of` timestamp rules |
| **Agent 1 JSON failures** | Local LLMs emit malformed output | Ollama JSON schema + Pydantic validation + retry once |
| **Scope creep** | Project never ships | Non-goals list is binding; v1 finish line in Success Criteria |
| **Build without learn** | Repo exists but interviews still fail | Success criteria include hand-write + explain drills, not just green CI |
| **Kafka ops complexity** | Weekend lost to infra debugging | Docker Compose with pinned images; replay mode bypassing live ingest for demos |

Detailed mitigations belong in the architecture doc and dev guides.

---

## Research Foundation

- `docs/2026-06-21_ai_engineering_in_demand_skills_and_financial_weekend_project_gemini_ai_brainstorming_conversation.md`

---

## Locked Decisions (v1)

| Decision | Choice |
|----------|--------|
| Repo visibility | Public |
| Build budget | 6–7 days max |
| Agent 2 algorithm | XGBoost |
| Training events | 500 (Option B) |
| Label definition | HIGH_RISK per Technical Approach |
| Tickers | 8 names (see above) |
| Historical news | Kaggle/CSV batch + RSS for live demo |
| Local LLM | Config-driven; see model table below | |

---

## When to Update This Doc

- Primary goal shifts (e.g., becomes a product not interview lab)
- Merge with Lowd Capital (explicitly rejected unless reconsidered)
- v1 ships — add “Maintenance” status and lessons learned
- Major stack swap (e.g., drop Kafka)

Do **not** update for implementation details — use architecture doc and dev guides.
