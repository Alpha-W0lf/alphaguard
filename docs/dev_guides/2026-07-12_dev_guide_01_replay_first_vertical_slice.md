# Dev Guide 01 — Replay-first vertical slice

**Date:** 2026-07-12  
**Repo:** `alphaguard`  
**Work item:** AlphaGuard v1 — first executable vertical slice  
**Stage that authored this:** Write dev guide  
**Status:** Ready for Ready-check / human review — **do not implement from this chat stage**

---

## Objective

Deliver the **thinnest end-to-end path** that proves AlphaGuard’s interview story:

**fixture headline → (optional Qdrant context) → Agent 1 structured JSON → Agent 2 XGBoost gate → LangSmith or Phoenix trace**, runnable via a single smoke/replay command **without live Kafka**.

Kafka + Qdrant Compose files may be added in this slice for later use, but **smoke must pass with Kafka stopped**.

---

## References (paths only)

- `alphaguard/docs/VISION.md`
- `alphaguard/docs/ARCHITECTURE.md`
- `second_brain/docs/2026-07-12_portfolio_vision_workspace_and_decisions.md`
- `second_brain/docs/2026-07-12_portfolio_public_projects_context_summary.md`
- `second_brain/docs/2026-07-12_portfolio_critical_review_staff_critique.md`
- `second_brain/docs/2026-07-12_alphaguard_architecture_handoff.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. Stack locks: `OLLAMA_MODEL` default `gemma4:e2b`; fallback `qwen3.5:4b`; LangSmith default + Phoenix fallback; FinBERT **batch offline only**; Compose Kafka+Qdrant; host Ollama; Option B ~500 events for training track; Agent 2 = XGBoost.  
2. **Replay-first:** `ALPHAGUARD_MODE=replay` bypasses live Kafka producers/consumers.  
3. No brokerage APIs; no Lowd Capital code; no second LLM auditor; no Loom requirement.  
4. Prefer ≤300 lines/file (max 400). Modules: `ingest/`, `agents/`, `ml/`, `infra/`, `api/`, `eval/`, `contracts`.  
5. Secrets only via `.env` from `.env.example`; never commit keys.  
6. Do not co-reside FinBERT with Kafka+Qdrant+Ollama on 16GB.  
7. Look-ahead leakage rules in ARCHITECTURE §6.4 are mandatory for any feature code.  
8. Smallest correct change: do **not** build live RSS, full 500-row polish, or INTERVIEW.md essay before smoke is green (stubs/docs placeholders OK).

---

## Ordered step checklist

### Phase A — Scaffold and contracts

- [ ] **A1.** Create Python package layout under `src/alphaguard/` with empty modules matching ARCHITECTURE layer map; add `pyproject.toml` (`uv`), ruff-friendly defaults, Python 3.11+.  
- [ ] **A2.** Add `.env.example` with at least: `OLLAMA_MODEL=gemma4:e2b`, `ALPHAGUARD_MODE=replay`, `ALPHAGUARD_RAG_MODE=qdrant|fixture`, LangSmith vars (optional), Phoenix toggle, Kafka/Qdrant URLs.  
- [ ] **A3.** Implement Pydantic contracts only: `NewsEvent`, `Agent1Proposal`, `Agent2Decision` per ARCHITECTURE §6. Unit-test valid + invalid fixtures (empty headline, bad action enum, confidence out of range).  
- [ ] **A4.** Add `data/fixtures/replay_events.jsonl` with ≥5 events across ≥3 tickers from the locked universe; include `event_id`, `headline`, `ticker`, `published_at`, `source=fixture`.  
- [ ] **A5.** Add `AGENTS.md` (short): locked stack, file size limits, replay-first, no secrets, point to VISION + ARCHITECTURE.

### Phase B — Infra stubs (Compose present; smoke independent)

- [ ] **B1.** Add `docker-compose.yml` with **pinned** Kafka + Qdrant images and healthchecks. Document `docker compose up -d` for later; do not require it for smoke.  
- [ ] **B2.** Add `make smoke` (or `uv run alphaguard smoke`) target that sets `ALPHAGUARD_MODE=replay` and **does not** start Kafka.  
- [ ] **B3.** Preflight script/check: verify Ollama reachable and `OLLAMA_MODEL` present; print clear pull command on failure; allow override to `qwen3.5:4b`.

### Phase C — Replay runner + RAG modes

- [ ] **C1.** Implement `ingest/replay.py` (name flexible): load fixture event(s) → emit internal `NewsEvent` → call pipeline façade. **No Kafka client required on this path.**  
- [ ] **C2.** Implement dual RAG mode:  
  - `fixture`: return curated context snippets from fixture sidecar (no Qdrant).  
  - `qdrant`: embed with sentence-transformers + upsert/query when Qdrant is up.  
  Smoke default may use `fixture` if that keeps 16GB stable; document how to flip to `qdrant`.  
- [ ] **C3.** Idempotent upsert by `event_id` when using Qdrant (safe re-run).

### Phase D — Agent 1 (LangGraph + Ollama)

- [ ] **D1.** LangGraph graph: retrieve context → prompt → structured JSON (Ollama structured outputs or JSON mode) → Pydantic validate.  
- [ ] **D2.** On validation failure: **exactly one** repair retry; then fail closed with structured error (do not invent HOLD silently).  
- [ ] **D3.** Trace Agent 1 spans via obs layer (LangSmith if configured else Phoenix).  
- [ ] **D4.** Local manual check: one fixture event yields valid `Agent1Proposal` with `gemma4:e2b` (or documented fallback).

### Phase E — Agent 2 (XGBoost gate) for the slice

- [ ] **E1.** Define feature vector matching ARCHITECTURE (FinBERT column may be **precomputed in fixture** for smoke — do not load FinBERT during smoke).  
- [ ] **E2.** For this slice, either: (preferred) train a **tiny** XGBoost on synthetic/fixture feature rows committed under `data/fixtures/`, or load a clearly labeled `fixture` model artifact. Full 500-event Option B builder is **out of this guide’s DoD** but schema must not conflict.  
- [ ] **E3.** `ml/gate.py`: map proposal + features → `approve|reject` + `risk_score` + `model_version`. Deterministic given fixed inputs.  
- [ ] **E4.** Unit-test: fixed features → stable decision; missing model file → fail closed with actionable message.

### Phase F — API façade + observability + smoke DoD wiring

- [ ] **F1.** FastAPI minimal: `GET /health`, `POST /replay` (body: `event_id` or raw fixture). CLI entrypoint preferred for smoke; API may wrap the same façade.  
- [ ] **F2.** Obs helper: select LangSmith vs Phoenix; always write a local run summary JSON under `artifacts/runs/` (gitignored) for offline proof.  
- [ ] **F3.** Wire `make smoke`: replay ≥1 fixture → print Agent1 JSON + Agent2 decision + trace backend name → exit 0.  
- [ ] **F4.** Add ≥20 golden eval stubs **or** a minimal `eval/golden_cases.jsonl` (≥5 in this slice, plan to grow to ≥20 before portfolio claim) checking schema validity + gate determinism. Document remaining eval debt if &lt;20.  
- [ ] **F5.** Root `README.md` stub: what it is, replay Quick Start, limitations, link to ARCHITECTURE; no false “complete” claims.  
- [ ] **F6.** Stop. Do not start live RSS producer, full FinBERT batch, or INTERVIEW.md deep FAQ in this guide unless smoke is already green and time remains — those belong in a later guide.

---

## Verification / Definition of Done (this guide)

**Done when all are true:**

1. `uv sync` (or documented install) works from a clean clone path.  
2. `make smoke` (or equivalent) exits 0 with **Kafka containers stopped**.  
3. Smoke prints valid Agent 1 JSON (schema-valid) and Agent 2 decision for a fixture event.  
4. Observability backend is either LangSmith **or** Phoenix (or documented local span dump if Phoenix install blocked — prefer Phoenix).  
5. `.env.example` complete; no secrets in git.  
6. Unit tests cover contracts + gate determinism + as-of helper if any price features exist.  
7. Compose file for Kafka+Qdrant exists with pinned images (even if unused by smoke).  
8. README does not claim live streaming demo as the default path; default is replay.  
9. No application path imports brokerage APIs or Lowd Capital.  
10. FinBERT is not loaded during smoke.

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
| Look-ahead leakage | Interview credibility kill | No future bars in any feature helper; tests |
| Local LLM JSON flakiness | Flaky smoke | Schema + one retry; fail closed; fallback model tag documented |
| Fake RAG theater | Staff critique repeat of Mechanic stub pattern | Document `fixture` vs `qdrant` modes honestly; prefer real Qdrant when up |
| Secret leakage | Key rotation / repo scrub | `.env.example` only; gitignore `.env`, `artifacts/` |
| Over-large files | Unmaintainable agent edits | 300/400 line rule in AGENTS.md |

---

## Edge-case handling (must appear in implementation or tests)

| Edge case | Expected behavior |
|-----------|-------------------|
| Empty / missing fixture file | Non-zero exit; clear error |
| Unknown `event_id` in `/replay` | 404-style error; no partial write claimed success |
| Ollama down | Preflight fails before graph run |
| Malformed LLM JSON twice | Run fails; obs records validation_error |
| Qdrant down + `RAG_MODE=qdrant` | Fail with hint to set `fixture` mode |
| Qdrant down + `RAG_MODE=fixture` | Smoke still passes |
| Duplicate smoke runs | Idempotent; same gate decision for fixed fixture features |
| Confidence as string `"0.8"` from model | Reject or coerce only if explicitly documented; prefer reject + retry |
| Ticker outside universe in fixture | Allow in replay with warning **or** reject — pick one rule and test it |
| LangSmith key invalid | Fallback Phoenix / local summary; smoke still 0 if pipeline OK |
| Missing gate model | Fail closed; message to train or use fixture model path |

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

## Honest readiness (authoring stage)

- This guide is executable by a later agent after **Ready check before code**.  
- Open human note: exact Kaggle/CSV slug for the eventual 500-event builder remains U4; fixtures unblock this slice.  
- Next stage: **Ready check before code** (not Implement from Write-dev-guide).  
