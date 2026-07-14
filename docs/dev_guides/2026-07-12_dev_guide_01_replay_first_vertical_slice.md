# Dev Guide 01 — Replay-first vertical slice

**Date:** 2026-07-12  
**Repo:** `alphaguard`  
**Work item:** AlphaGuard v1 — first executable vertical slice  
**Stage that authored this:** Write dev guide  
**Status:** Implement complete (pass-8); Review pass-9 shippable. Guide DoD met with default `OLLAMA_MODEL=gemma4:e2b` + fixture RAG (Ollama ≥0.20+). Documented D1 fallback remains `qwen3.5:4b` if pull returns 412 on older Ollama.

---

## Objective

Deliver the **thinnest end-to-end path** that proves AlphaGuard’s interview story:

**fixture headline → `PipelineService` → (optional Qdrant / fixture `RetrievalHit`s with as-of filter) → Agent 1 structured JSON (`BUY|HOLD|PASS`) → Agent 2 XGBoost downside-risk score + deterministic policy → local run summary (+ LangSmith/Phoenix best-effort)**, runnable via a single smoke/replay command **without live Kafka**.

Kafka + Qdrant Compose files may be added in this slice for later use, but **smoke must pass with Kafka stopped**.

---

## Learning note — SSOT

**SSOT** = **single source of truth**: one document that wins when two docs disagree. Here, **`ARCHITECTURE.md` is the contracts/how SSOT** (schemas, failure modes, OOU reject, as-of rules). **`VISION.md` is the product/why SSOT**. If this guide’s wording drifts, follow ARCHITECTURE — do not invent a softer fixture rule.

---

## References (paths only)

- `alphaguard/docs/VISION.md` (product / why SSOT)
- `alphaguard/docs/ARCHITECTURE.md` (contracts / how SSOT; pass-4; AG1–AG3 binding)
- `second_brain/docs/2026-07-12_portfolio_vision_workspace_and_decisions.md` (AG1–AG3)
- `second_brain/docs/2026-07-12_alphaguard_architecture_pass4_handoff.md`
- `second_brain/docs/2026-07-12_alphaguard_ready_check_pass6.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. Stack locks: `OLLAMA_MODEL` default `gemma4:e2b`; fallback `qwen3.5:4b`; LangSmith + Phoenix **best-effort**; **local run summary mandatory**; FinBERT **batch offline only**; Compose Kafka+Qdrant; host Ollama; Option B ~500 events for training track; Agent 2 = XGBoost **downside-risk scorer** + deterministic policy (AG1).  
2. **Replay-first:** `ALPHAGUARD_MODE=replay` bypasses live Kafka producers/consumers.  
3. No brokerage APIs; no Lowd Capital code; no second LLM auditor; no Loom; **no neural reranker**; Agent 1 RAG = simple top-k + as-of filter only.  
4. Prefer ≤300 lines/file (max 400). Modules: `ingest/`, `pipeline/`, `agents/`, `ml/`, `infra/`, `api/`, `eval/`, `contracts/` (top-level only).  
5. Secrets only via `.env` from `.env.example`; never commit keys.  
6. Do not co-reside FinBERT with Kafka+Qdrant+Ollama on 16GB; honor ARCHITECTURE §16 resource modes.  
7. Unified as-of + `RetrievalHit` rules in ARCHITECTURE §7.3 / §8 (AG3) are mandatory for any feature or RAG code.  
8. Labels for any training code: **forward downside return only** (AG2); never OR volatility into the learned label.  
9. Smallest correct change: do **not** build live RSS, full 500-row polish, or INTERVIEW.md essay before smoke is green (stubs/docs placeholders OK).

---

## Ordered step checklist

### Phase A — Scaffold and contracts

- [x] **A1.** Create Python package layout under `src/alphaguard/` with empty modules matching ARCHITECTURE layer map; add `pyproject.toml` (`uv`), ruff-friendly defaults, Python 3.11+.  
- [x] **A2.** Add `.env.example` with at least: `OLLAMA_MODEL=gemma4:e2b`, `ALPHAGUARD_MODE=replay`, `ALPHAGUARD_RAG_MODE=qdrant|fixture`, LangSmith vars (optional), Phoenix toggle, Kafka/Qdrant URLs.  
- [x] **A3.** Implement Pydantic contracts per ARCHITECTURE §7: `NewsEvent`, `RetrievalHit`, `Agent1Proposal` (`BUY|HOLD|PASS` only — reject `SELL`), `Agent2Decision` (includes `downside_risk_score` + policy fields), run envelope, and a minimal fixture **model bundle manifest**. Unit-test valid + invalid fixtures (empty headline, `SELL`, confidence out of range, future `available_at`).  
- [x] **A4.** Add `data/fixtures/replay_events.jsonl` with ≥5 events across ≥3 tickers from the locked universe; include `event_id`, `headline`, `ticker`, `published_at`, `source=fixture`. Add fixture retrieval sidecar hits with honest `available_at`. **Reject** out-of-universe tickers on load (ARCHITECTURE §7.1 — no silent remap).  
- [x] **A5.** Add `AGENTS.md` (short): locked stack, AG1–AG3 one-liners, file size limits, replay-first, no secrets, point to VISION + ARCHITECTURE.

### Phase B — Infra stubs (Compose present; smoke independent)

- [x] **B1.** Add `docker-compose.yml` with **pinned** Kafka + Qdrant images and healthchecks. Document `docker compose up -d` for later; do not require it for smoke.  
- [x] **B2.** Add `make smoke` (or `uv run alphaguard smoke`) target that sets `ALPHAGUARD_MODE=replay` and **does not** start Kafka.  
- [x] **B3.** Preflight script/check: verify Ollama reachable and `OLLAMA_MODEL` present; print clear pull command on failure; allow override to `qwen3.5:4b`.

### Phase C — Replay runner + PipelineService + RAG modes

- [x] **C1.** Implement `ingest/replay.py` (name flexible): load fixture event(s) → emit internal `NewsEvent` → call **`PipelineService.run`**. **No Kafka client required on this path.**  
- [x] **C2.** Implement `pipeline/` as the sole orchestrator (ordering, identity stamp, retries, envelope write). API and future Kafka consumer must call the same façade.  
- [x] **C3.** Implement dual RAG mode returning `RetrievalHit[]`, owned by **`PipelineService`** (via `rag/`):  
  - `fixture`: curated hits from fixture sidecar (no Qdrant); each hit has `available_at`.  
  - `qdrant`: embed with sentence-transformers + upsert/query when Qdrant is up; **filter `available_at <= published_at`**.  
  Smoke default may use `fixture` (`resource_mode=replay_fixture`) if that keeps 16GB stable; document how to flip to `qdrant`. Simple top-k only — no reranker.  
- [x] **C4.** Idempotent upsert by `event_id` / `document_id` when using Qdrant (safe re-run). Unit-test that a future `available_at` hit is dropped.

### Phase D — Agent 1 (LangGraph + Ollama)

- [x] **D1.** LangGraph graph: **consume** `RetrievalHit[]` already loaded into state by `PipelineService` → prompt → structured JSON (Ollama structured outputs or JSON mode) → Pydantic validate (`BUY|HOLD|PASS` only). Do **not** open a second retrieve path.  
- [x] **D2.** On validation failure: **exactly one** repair retry; then fail closed with structured error (do not invent HOLD silently; do not accept `SELL`).  
- [x] **D3.** `PipelineService` overwrites `event_id`/`ticker` from the input event before gating; log identity mismatch if LLM differed.  
- [x] **D4.** Trace Agent 1 spans via obs layer (local summary always; LangSmith/Phoenix best-effort fail-open).  
- [x] **D5.** Local manual check: one fixture event yields valid `Agent1Proposal` with `gemma4:e2b` (or documented fallback).

### Phase E — Agent 2 (downside scorer + policy) for the slice

- [x] **E1.** Define feature vector matching ARCHITECTURE §7.5 (FinBERT column may be **precomputed in fixture** for smoke — do not load FinBERT during smoke). Include `feature_as_of` on fixture feature rows.  
- [x] **E2.** For this slice, either: (preferred) train a **tiny** XGBoost downside scorer on synthetic/fixture feature rows, or load a clearly labeled `bundle_kind=fixture` model **bundle + manifest**. Full 500-event Option B builder is **out of this guide’s DoD** but schema/manifest must not conflict.  
- [x] **E3.** `ml/gate.py`: score → `downside_risk_score` → deterministic policy (§7.4) → `approve|reject` + `model_version`/`bundle_id`. Deterministic given fixed inputs.  
- [x] **E4.** Unit-test: fixed features → stable decision; BUY rejected when score ≥ threshold; HOLD/PASS approve; missing/skewed manifest → fail closed with actionable message.

### Phase F — API façade + observability + smoke DoD wiring

- [x] **F1.** FastAPI minimal: `GET /health` (per-dependency statuses per §16), `POST /replay` (body: `event_id` or raw fixture). CLI entrypoint preferred for smoke; API wraps `PipelineService` only.  
- [x] **F2.** Obs helper: **always** write local run envelope under `artifacts/runs/` (gitignored); LangSmith/Phoenix fail-open.  
- [x] **F3.** Wire `make smoke`: replay ≥1 fixture → print Agent1 JSON + Agent2 decision (incl. downside score) + obs backend status → exit 0.  
- [x] **F4.** Add ≥20 golden eval stubs **or** a minimal `eval/golden_cases.jsonl` (≥5 in this slice, plan to grow to ≥20 before portfolio claim) checking schema validity, identity preservation, as-of/retrieval invariants, gate determinism. Document remaining eval debt if &lt;20.  
- [x] **F5.** Root `README.md` stub: what it is, replay Quick Start, limitations, link to ARCHITECTURE; call this a **vertical slice**, not “v1 complete.”  
- [x] **F6.** Stop. Do not start live RSS producer, full FinBERT batch, or INTERVIEW.md deep FAQ in this guide unless smoke is already green and time remains — those belong in a later guide.

---

## Verification / Definition of Done (this guide)

**Done when all are true:**

1. `uv sync` (or documented install) works from a clean clone path.  
2. `make smoke` (or equivalent) exits 0 with **Kafka containers stopped**.  
3. Smoke prints valid Agent 1 JSON (`BUY|HOLD|PASS` only) and Agent 2 decision (incl. `downside_risk_score` + policy outcome) for a fixture event.  
4. Local run envelope always written; LangSmith/Phoenix may be skipped/failed without failing a valid pipeline.  
5. `.env.example` complete; no secrets in git.  
6. Unit tests cover contracts + gate policy + as-of/`RetrievalHit` future-hit rejection + identity overwrite.  
7. Compose file for Kafka+Qdrant exists with pinned images (even if unused by smoke).  
8. README does not claim live streaming demo as the default path; default is replay; fixture bundle ≠ Option B proof.  
9. No application path imports brokerage APIs or Lowd Capital; no neural reranker.  
10. FinBERT is not loaded during smoke.  
11. Gate loads via model **bundle + manifest** (`bundle_kind=fixture` acceptable for this slice).

**Explicitly not required for this guide’s DoD:**

- Full 500-event parquet trained production model  
- Live RSS → Kafka consumer E2E  
- INTERVIEW.md 15+ FAQ complete  
- Public GitHub polish / LICENSE finalization (may stub)  
- CI on GitHub Actions (nice-to-have)

---

## Blast radius and risks

| Risk | Blast radius | Mitigation in steps |
|------|----------------|---------------------|
| 16GB RAM thrash | Machine unusable; false “LLM broken” | Smoke without Kafka; RAG `fixture` mode; FinBERT never in smoke; sequential Compose |
| Kafka rabbit hole | Burns multi-day budget before agents exist | Kafka optional for smoke; Compose only in Phase B |
| Scope creep to full Option B | Delays first credible demo | E2 allows fixture model; 500-event builder deferred |
| Look-ahead leakage | Interview credibility kill | AG3 as-of + RetrievalHit filter; tests reject future data |
| Action/label incoherence | Misleading ML interview story | AG1 policy table; AG2 forward-return-only labels; no SELL |
| Local LLM JSON flakiness | Flaky smoke | Schema + one retry; fail closed; fallback model tag documented |
| Fake RAG theater | Staff critique repeat of Mechanic stub pattern | Document `fixture` vs `qdrant` modes honestly; prefer real Qdrant when up; no ranking showcase |
| Secret leakage | Key rotation / repo scrub | `.env.example` only; gitignore `.env`, `artifacts/` |
| Over-large files | Unmaintainable agent edits | 300/400 line rule in AGENTS.md |

---

## Edge-case handling (must appear in implementation or tests)

| Edge case | Expected behavior |
|-----------|-------------------|
| Empty / missing fixture file | Non-zero exit; clear error |
| Unknown `event_id` in `/replay` | 404-style error; no partial write claimed success |
| Ollama down | Preflight fails before graph run |
| Malformed LLM JSON twice | Run fails; envelope records validation_error |
| LLM emits `SELL` | Reject / repair; never approve |
| LLM wrong `ticker`/`event_id` | Overwritten from input event; mismatch logged |
| Retrieval hit with future `available_at` | Dropped before prompt |
| Qdrant down + `RAG_MODE=qdrant` | Fail with hint to set `fixture` mode |
| Qdrant down + `RAG_MODE=fixture` | Smoke still passes |
| Duplicate smoke runs | Idempotent; same gate decision for fixed fixture features |
| Confidence as string `"0.8"` from model | Reject or coerce only if explicitly documented; prefer reject + retry |
| Ticker outside universe in fixture | **Reject** (ARCHITECTURE §7.1) — do not silently remap or warn-and-continue; unit-test OOU fixture load fails closed |
| LangSmith key invalid | Envelope records adapter failure; local summary remains; smoke still 0 if pipeline OK |
| Missing / skewed gate manifest | Fail closed; message to train or use fixture bundle path |

---

## Suggested verification commands (implementer)

```bash
# Kafka must remain down for this check
docker compose ps || true
uv sync
cp -n .env.example .env
# ensure Ollama running with gemma4:e2b or OLLAMA_MODEL=qwen3.5:4b
make smoke
uv run pytest -q
```

Expected smoke signal: one JSON proposal, one gate decision, tracer name, exit code 0.

---

## Stop conditions for the implementer

- Stop when this guide’s DoD is met.  
- Do **not** expand into live Kafka E2E, full 500-event training, or packaging polish without a new guide / human gate.  
- If a stack change seems required, **stop and ask** — do not reopen VISION locks.

---

## Honest readiness (post Implement + Review)

- Guide DoD **met** (Implement pass-8; Review pass-9 **shippable**). Default smoke = `OLLAMA_MODEL=gemma4:e2b` + `ALPHAGUARD_RAG_MODE=fixture`.  
- This file’s Phase A–F checkboxes stay checked because the slice landed — do **not** re-open Implement from this guide.  
- Open human notes for **later guides** only: U4 Kaggle/CSV slug; Option B train; Kafka E2E; eval ≥20; real LangSmith/Phoenix spans; stable Qdrant point ids (`hash(event_id)` residual).  
- **Not** “v1 complete.” Fixture bundle ≠ Option B proof.