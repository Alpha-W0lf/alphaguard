# AlphaGuard: Vision Document

**Purpose:** Build a bounded, public reference pipeline that teaches and demonstrates senior AI/data-engineering skills so Tom can pass technical interview rounds—not just recruiter screens.

**Status:** **Bounded minimum viable build complete** (guides 01–08); **production hardening and deeper live evaluation incomplete.** Finish line = **local + CI** (not a hosted service). Score doneness on **what is built** — **not** interview rehearsal. Still **not** eval-complete / **not** a production risk model / **not** “interview fluency proven.” Guide 04 = Kafka+Qdrant thin integration; Guide 06 = Yahoo RSS poll CLI (Yahoo may flake); Guide 07 = LangSmith Client emit when configured; Guide 08 = Phoenix OTEL chain span when `PHOENIX_ENABLED`; default smoke still Kafka-down **fixture** (never requires LangSmith key or Phoenix collector). Finance claims surface: [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md). **LICENSE:** PolyForm-NC 1.0.0 (source-available / non-commercial — not OSI open source / not MIT; commercial use → contact copyright holder).

**Last Updated:** July 21, 2026 (Align finish-line wording + finance honesty; Interview-prep boxes still separate / unchecked)

**Owner:** Tom

**Guide:** Structured per [`second_brain/docs/guides/meta_creating_vision_docs.md`](../../second_brain/docs/guides/meta_creating_vision_docs.md). This file is the **product / why** decision framework. Binding contracts, as-of rules, and gate policy live in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Program locks **AG1–AG3:** `second_brain/docs/2026-07-12_portfolio_vision_workspace_and_decisions.md`.

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

**AlphaGuard** is a stateful multi-agent financial research pipeline that ingests news, retrieves context via RAG, proposes structured trade ideas (Agent 1), and gates them through a supervised ML **downside-risk scorer + deterministic policy** (Agent 2)—with LangSmith/Phoenix best-effort tracing and a mandatory local run summary.

It simulates institutional “analyst + risk” separation using tools employers recognize in mid-2026: **Kafka, Qdrant, LangGraph, Ollama, LangSmith, FastAPI, XGBoost**.

### How I'll Use It

1. **Build** the pipeline locally on M2 Pro (16GB) with Docker Compose.
2. **Interview prep (optional, separate):** spoken walkthrough / explain drills using packaging docs — **not** a build gate; Tom does not treat daily hand-coding as a project requirement.
3. **Share** public GitHub repo + README/GETTING_STARTED + **local run summary** screenshots in `docs/` — no Loom or required live demo. Real LangSmith/Phoenix evidence only when a configured run is actually captured (not required for packaging).
4. **Defend** architecture, tradeoffs, leakage controls, and failure modes in system design interviews.

### Key Capabilities

1. **Event-driven ingestion:** Financial headlines flow through Kafka; consumers embed and upsert into Qdrant (rolling context window). Replay fixtures bypass live Kafka for demos.
2. **Agent 1 — LLM Analyst:** LangGraph + local Ollama (config-driven; see Technical Approach) consumes as-of-filtered RAG hits and outputs structured JSON (`action` ∈ `BUY|HOLD|PASS`, `confidence`, `rationale`). Application owns `event_id`/`ticker` identity — LLM identity fields are overwritten. `SELL` is unsupported in v1.
3. **Agent 2 — Downside-risk gate:** XGBoost emits a **downside risk score**; a **deterministic policy** maps `(action, score[, optional vol veto]) → approve|reject`. Trained on **~500 historical headline events** (Option B) with **forward-downside labels only** (AG2)—not Agent 1 backtest labels, and not volatility-as-label.
4. **LLMOps observability:** Local run summary always (mandatory); LangSmith and Phoenix are optional fail-open adapters when configured.
5. **Interview artifacts:** README architecture diagram, `FAQ.md` FAQ, optional replay demo of cached end-to-end runs.

### Workflow Integration

```
Study job posting → Map skills gap → Build/rehearse AlphaGuard component →
Point interviewers at public repo + docs artifacts → Whiteboard same architecture live
```

AlphaGuard does **not** run in production, manage capital, or connect to live brokerage APIs.

---

## Design Principles

### 1. Finish Line Over Feature Count

**Rationale:** Scope creep kills weekend/week projects and delays interview prep.

**In Practice:** v1 is done when one headline flows end-to-end with **local run summary** + ML gate + public README. LangSmith/Phoenix spans are optional when configured. No cloud Kafka deploy, no fine-tuning, no hybrid search, no second LLM agent.

### 2. Learn by Building, Prove by Explaining

**Rationale:** The repo gets the interview; **fluency** passes the interview.

**In Practice:** Build with AI-native discipline (specs, tests, review). Interview fluency is a **separate initiative** — optional spoken walkthrough / hand-coding drills using `FAQ.md` and `docs/WALKTHROUGH_10MIN.md`. Those drills are **not** build blockers and are **not** scored as portfolio build %.

### 3. Hybrid AI + ML (Not LLM-Only)

**Rationale:** Senior AI/DE roles expect both agentic systems and tabular ML discipline.

**In Practice:** Agent 1 = LLM (`BUY|HOLD|PASS`). Agent 2 = XGBoost **downside-risk scorer** + deterministic approve/reject policy on engineered features. README states clearly: Agent 2 is a **regime / downside-risk gate**, not an alpha model.

### 4. Honest Data Science

**Rationale:** Interviewers will probe leakage, labels, and train/test methodology.

**In Practice:** ~500 events, time-based split **before** any threshold fit, features computed only from completed sessions at/before headline time (`feature_as_of`), labels from **forward downside return only** (AG2). Volatility is a predictor and/or deterministic BUY veto — never a learned-label branch. Document limitations openly.

### 5. Public Shell, No Secret Sauce

**Rationale:** Protect [Lowd Capital](../lowd_capital/docs/VISION.md) proprietary logic.

**In Practice:** Public repo. No live keys in git. No strategies that overlap with private trading research.

### 6. AI-Native Build, Human-Validated Ship

**Rationale:** Tom builds with AI agents; quality comes from specs, tests, and review—not typing every line.

**In Practice:** Spec-first and test-first for ML gate JSON schema and feature pipeline. Repo-level agent guidance (`AGENTS.md`) enforces simplicity and file size limits.

---

## Implementation progress (honest — do not inflate)

| Milestone | Status | Evidence |
|-----------|--------|----------|
| Guide 01 — replay-first vertical slice | **Done** (Implement pass-8; Review pass-9 shippable) | `make smoke` + fixture RAG + `gemma4:e2b`; local envelope; fixture `bundle_kind=fixture` |
| Guide 02 — interview packaging | **Done** | `FAQ.md`, `GETTING_STARTED.md`, `docs/assets/` |
| Guide 03 — eval harness ≥21 goldens | **Done** (Implement pass-38) | `eval/golden_cases.jsonl` + `src/alphaguard/eval/` parametrized façades; fixture-path OOU + tmp vol-veto; **not** live-Ollama rates |
| Option B ~500-event train + real metrics | **Train CLI landed (Guide 05b); lab metrics only** | `scripts/train_option_b_gate.py` → `data/derived/model_bundle_option_b/` (`bundle_kind=option_b`, nested time-HPO). Default smoke still **fixture**. Not production risk model; lab test F1 may be weak/noisy — see [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md) |
| Live RSS → Kafka E2E | **Thin operator path landed** (Guide 06) | `alphaguard rss poll` (Yahoo RSS → produce); Guide 04 Kafka path reused; **not** 24/7 reliability / not agent-on-consume |
| Portfolio-ready interview lab | **Bounded MV build complete; interview prep separate** | Guides 01–08 built (local + CI); production hardening / deeper live eval incomplete; walkthrough / daily hand-coding = **Interview prep** below — not build % |

README / AGENTS / [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md): **bounded MV complete** ≠ production risk model ≠ eval-complete ≠ interview fluency proven.

## Success Criteria

### Minimum Viable (v1 build Done)

Score portfolio **build** doneness on these boxes only (Tom lock 2026-07-18):

- [x] `docker compose up` runs Kafka + Qdrant locally *(operator path documented in README; smoke still Kafka-down)*
- [x] 500 headline events dataset **builder** landed (`scripts/build_training_events.py` → `data/derived/training_events.parquet`; Guide 05a) — regenerate locally; raw dump not in git
- [x] XGBoost downside-risk scorer trained with time-based holdout + train-only threshold fit; metrics in bundle manifest + TRAINING_DATA *(default smoke still fixture; lab-scale test F1 is noisy — not production)* — **Guide 05b**
- [x] One **replayed** fixture headline flows: ingest → RAG → Agent 1 → Agent 2 → local run summary *(Guide 07–08: LangSmith = real fail-open spans when tracing+key; Phoenix = real fail-open spans when `PHOENIX_ENABLED`; default smoke has both `skipped`)*
- [x] Public GitHub polish with architecture diagram, stack table, and claim hygiene *(README mermaid + Stack + Deeper docs / FINANCE_HONESTY + sales-first proof card in `docs/assets/`; Guide 02 + 2026-07-31 README sales-first pass)*
- [x] `FAQ.md` with 15+ gotcha Q&A *(17 themes as of 2026-07-17 Align)*

### Interview prep (separate initiative)

**Not** build blockers. **Not** scored in portfolio build %. Do **not** invent ticks that imply Tom finished rehearsal.

- [ ] 10-minute unprompted architecture walkthrough without opening code *(outline: `docs/WALKTHROUGH_10MIN.md` — optional rehearsal; Tom has not marked complete)*
- [ ] 15–30 min/day hand-coding habit *(deferred — Tom does not run this as a project gate)*

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
- `SELL` proposals in v1 (AG1 — unsupported)
- Volatility as a learned-label branch (AG2 — predictor / optional policy veto only)
- Neural reranker / hybrid RRF ranking showcase for Agent 1 RAG
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
| Local LLM | Ollama + config-driven model (**default `gemma4:e2b`**) | Modern edge model; swappable |
| Embeddings | `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) | Local, fast; separate from agent LLM |
| LLMOps | LangSmith (default) + Phoenix local fallback | Market leader for traces; offline/no-signup path |
| API | FastAPI | Thin trigger/replay endpoint |
| ML Gate | XGBoost downside scorer + scikit-learn + deterministic policy | Fast local training; DE interview staple; AG1 |
| Sentiment features | FinBERT inference (HF) | Financial domain signal without training |
| Prices | yfinance | Free OHLCV for features and labels |
| Packaging | Docker Compose | One-command local infra |

### Agent 2 Data Strategy (Option B — Locked for v1)

**Training corpus:** 500 headline events aligned to tickers and trading days.

**Per-event features (AG3 — last completed session at/before event; record `feature_as_of`):**
- FinBERT sentiment score (batch offline)
- `volatility_20d`, `return_5d_prior`, `return_20d_prior` for ticker (**predictors only**)
- `spy_return_5d` (market context)
- Optional: headline source bucket, word count

**Label (training only — AG2; superseded vol-OR definition removed):**
- `label_high_risk = 1` iff `fwd_return_5d < -0.03`; else `0`
- `fwd_return_5d` = return from the **first completed session close at or after** the event’s calendar session to the close **5 trading sessions later** (labels may use post-event closes; features must not)
- `volatility_20d` is **never** a branch of the learned label; it may remain a feature and/or an optional **deterministic BUY veto** outside the learned target

**Split / thresholds:** Time-ordered 80/20 (no random shuffle). **Split first**, then fit `score_threshold` on **train only** by maximizing train F1 on `proba_high_risk` (optional `vol_veto_threshold` also train-only); freeze into the model bundle manifest.

**Inference (AG1):** Agent 1 JSON (`BUY|HOLD|PASS`) + as-of features → XGBoost `downside_risk_score` (`proba_high_risk`) → deterministic policy → `approve` / `reject`. Application stamps `event_id`/`ticker`. Local run summary always; LangSmith/Phoenix best-effort.

**Headline sources (default):** Primary = curated CSV/Kaggle financial news archive for historical 500; live demo = RSS (Yahoo Finance). Document exact dataset in README.

**Ticker universe (default):** AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ (8 tickers).

### Local LLM Selection (Config-Driven, Not Hardcoded)

**Purpose of the model:** Demonstrate Agent 1 structured JSON + RAG on **commodity 16GB hardware** — not SOTA chat quality. Tag is always `OLLAMA_MODEL` (never hardcoded).

**Reality check (2026-07-12):**
- **Qwen 3.7** — not available as open local weights on Ollama (API-only).
- **Qwen 3.6** — open, but **no small dense 4B**; 27B / 35B-A3B only → not a concurrent default with Kafka+Qdrant on 16GB.
- **Qwen 3.5:4b** — small (~3.4GB) and comfortable with Docker, but **not the newest** family.
- **Gemma 4** — current Google open family on Ollama; edge tags `gemma4:e2b` (~7.2GB) and `gemma4:e4b` (~9.6GB); agent/tooling-oriented; multimodal-capable (we still use **text-only** for AlphaGuard Agent 1).

**Locked default (portfolio / 16GB M2 Pro):** `gemma4:e2b`

| Priority | Ollama tag | Approx. size | Role |
|----------|------------|--------------|------|
| **1 — Default** | `gemma4:e2b` | ~7.2GB | Modern edge model; agent-oriented; use with **sequential RAM** (see below) |
| **2 — Low-RAM / concurrent fallback** | `qwen3.5:4b` | ~3.4GB | Best headroom if Compose + IDE + browser must stay hot |
| 3 — Optional quality (infra stopped) | `gemma4:e4b` | ~9.6GB | Only when Kafka/Qdrant are down or machine has more RAM |
| Avoid as default | `qwen3.6:*`, `gemma4:12b+`, `gemma4:26b/31b` | ≥17GB class | Breaks 16GB + Docker + background apps |

**RAM operating rule:** Prefer **not** holding Kafka + Qdrant + Ollama + FinBERT all resident. Replay demos may stop unused containers; training/feature jobs run FinBERT offline in batch.

**Interview story:** *"Default is `gemma4:e2b` for a current open edge model. Config allows `qwen3.5:4b` when reviewers need maximum concurrent headroom. We do not chase Qwen 3.6/3.7 large-only locals on 16GB."*

### Key Patterns

- **Brains never call exchange APIs** — no execution layer in v1
- **Structured JSON contracts** between agents with schema validation (`BUY|HOLD|PASS` only; `SELL` rejected)
- **Application owns identity** — `event_id` / `ticker` from the input event, not the LLM
- **Separation of concerns:** `ingest/`, `pipeline/`, `agents/`, `ml/`, `infra/` modules; contracts in `ARCHITECTURE.md`

### Automation

- Manual CLI / FastAPI trigger for demos
- No 24/7 daemon required for v1

### Sharing Strategy

| Artifact | Purpose |
|----------|---------|
| Public GitHub (pinned) | Primary proof |
| README + GETTING_STARTED | Skim + clone-and-run path |
| Local run-summary screenshots in `docs/` (mandatory baseline) | LLMOps proof without video; optional LangSmith/Phoenix only from a real configured run |
| Replay/fixture smoke output | Proof the path runs without live feeds |
| `FAQ.md` | Deep-dive prep + send before technical round |

No Loom. No required live hosted demo. No full cloud deploy required for v1.

---

## Implementation Risks (Vision-Level)

| Risk | Why it matters | Mitigation |
|------|----------------|------------|
| **16GB RAM contention** | Kafka + Qdrant + Ollama + FinBERT together can swap-thrash | Run services sequentially during dev; limit concurrent containers; pick smallest viable LLM quant |
| **500-event dataset quality** | Bad alignment → weak ML gate → embarrassing interview story | Document schema; manual spot-check 20 rows; time-based split only |
| **Look-ahead leakage** | Features accidentally use future prices | Architecture doc defines strict `as-of` timestamp rules |
| **Agent 1 JSON failures** | Local LLMs emit malformed output | Ollama JSON schema + Pydantic validation + retry once |
| **Scope creep** | Project never ships | Non-goals list is binding; v1 finish line in Success Criteria |
| **Build without interview fluency** | Repo exists but interviews still fail | Keep build MV honest; optional Interview-prep drills stay separate (not a build gate) |
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
| Agent 1 actions (AG1) | `BUY \| HOLD \| PASS` only; **`SELL` unsupported** |
| Agent 2 role (AG1) | XGBoost **downside-risk scorer** + deterministic approve/reject policy |
| Training events | ~500 (Option B) |
| Label definition (AG2) | `label_high_risk = 1` iff `fwd_return_5d < -0.03`; **no volatility OR-branch** |
| As-of (AG3) | UTC event clock; exchange calendar; completed-session features + `feature_as_of`; retrieval `available_at <= published_at` |
| Tickers | 8 names (see above); reject out-of-universe in v1 training/fixtures |
| Historical news | Kaggle/CSV batch + RSS for live demo |
| Local LLM | **Default `gemma4:e2b`**; fallback `qwen3.5:4b`; config `OLLAMA_MODEL` |
| Observability | **Local run summary mandatory**; LangSmith + Phoenix optional fail-open when configured; **local-envelope screenshots** required for packaging (not fabricated cloud-trace UI) |
| FinBERT concurrency | **Batch offline** — do not require FinBERT resident with Kafka+Qdrant+Ollama on 16GB |
| Sharing | Public GitHub + docs; **no Loom**; no required live hosted demo |

**Program SSOT (AG1–AG3):** `second_brain/docs/2026-07-12_portfolio_vision_workspace_and_decisions.md`  
**Contracts SSOT:** [`ARCHITECTURE.md`](./ARCHITECTURE.md) — do not reintroduce superseded label/action text here.

---

## When to Update This Doc

- Primary goal shifts (e.g., becomes a product not interview lab)
- Merge with Lowd Capital (explicitly rejected unless reconsidered)
- v1 ships — add “Maintenance” status and lessons learned
- Major stack swap (e.g., drop Kafka)

Do **not** update for implementation details — use architecture doc and dev guides.
