# Dev Guide 07 — LangSmith real fail-open spans (thin)

**Date:** 2026-07-17  
**Repo:** `alphaguard`  
**Work item:** Guide 07 — replace LangSmith envelope status theater with real fail-open span emit  
**Stage that authored this:** Write-dev-guide (pass 123)  
**Status:** **Ready for Ready-check / Implement** (no code in this Write stage)

**Context SSOT:** `alphaguard/docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md`  
**Hub lock:** `second_brain/docs/2026-07-17_hub_fanin_ag_gather_authorize_write_pass123.md`  
**Prerequisite:** Guides 01–06 shippable. Local run envelope real (`obs/summary.py`). Default smoke remains fixture / Kafka-down.

**Human locks (pass 123 — do not reopen):**

| Lock | Value |
|------|--------|
| Scope | **LangSmith real fail-open spans only** |
| Phoenix | **Stub stays** — no real Phoenix spans in this guide; docs stay honest |
| Smoke | Fixture / Kafka-down default; **never** requires LangSmith API key |
| MV walkthrough / daily-prep | **Human-only** — do not invent ticks |
| Agent-on-consume / Optuna / brokerage / Lowd | **Out** |

---

## Objective

Close the LLMOps honesty gap: today `best_effort_adapters` sets `obs.langsmith=ok` when a key is present **without emitting any SDK span**. Guide 07 makes `ok` mean **at least one real LangSmith run/span was successfully created** (or records honest `skipped`/`failed`), while keeping **local run summary mandatory** and **fail-open** relative to pipeline approve/reject.

**Success signal:** Unit tests prove (1) tracing off → `skipped`, (2) mocked successful emit → `ok` + run id in envelope extras, (3) mocked SDK/network failure → `failed` and pipeline status may be `degraded` but decision unchanged; `make smoke` with default env (no key) still green fixture path.

---

## Learning notes (new for this guide)

1. **Fail-open telemetry** — Observability must not rewrite business outcomes. Tracer down → envelope `failed` / run `degraded`; gate decision stays valid.  
2. **Status field ≠ span** — Setting `ok` from key presence is theater. Interviewers ask what was emitted.  
3. **Local envelope remains SSOT for clone path** — LangSmith is optional enrichment when configured.  
4. **Phoenix deferred** — Keep stub path; do not claim dual-backend maturity in this guide.

---

## References (paths only)

- `alphaguard/docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§7.7 envelope, §10 LangSmith failure, **§13 Observability**)
- `alphaguard/docs/VISION.md` (LLMOps; MV human boxes)
- `alphaguard/src/alphaguard/obs/summary.py` (current theater)
- `alphaguard/src/alphaguard/pipeline/service.py` (`build_obs_status`, degraded-on-adapter-failed)
- `alphaguard/src/alphaguard/contracts/envelope.py` (`ObsStatus`, `extras`)
- `alphaguard/src/alphaguard/config.py` (`langsmith_*`)
- `alphaguard/.env.example` (`LANGSMITH_*`)
- `alphaguard/{README,GETTING_STARTED,INTERVIEW,AGENTS}.md`
- `alphaguard/docs/assets/README.md` (stub screenshot honesty)
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **LangSmith thin adapter only.** No Phoenix real spans. No agent-on-consume. No smoke default flip. No Optuna/W&B.  
2. **Local envelope remains mandatory** — write `artifacts/runs/<run_id>.json` regardless of LangSmith.  
3. **Fail-open (DF-6 / §13):** SDK import error, auth error, timeout, or network failure → `obs.langsmith=failed`; must **not** flip `approve|reject` or force pipeline `error` solely due to tracer. Existing `degraded` when success+adapter failed stays OK.  
4. **Smoke never requires LangSmith key** — default `.env` / CI: tracing off → `skipped`; smoke green.  
5. **No secrets in git** — never commit API keys; never print full key in logs.  
6. Prefer ≤300 lines/file (hard max 400). Prefer new thin module `obs/langsmith_adapter.py` + slim changes to `summary.py` / `pipeline/service.py`.  
7. Docs honesty same delivery; **never** tick VISION MV walkthrough / daily-prep boxes.  
8. Do **not** fabricate LangSmith UI screenshots. Optional real UI capture is **out** of DoD (envelope + unit mocks suffice).

---

## Soft pins (locked — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Dependency | Add **`langsmith`** to project deps (`pyproject.toml` / `uv sync`). Import inside adapter try/except so missing install fails open as `failed` when tracing requested, or document required dep for configured mode |
| When to attempt emit | `settings.langsmith_tracing is True` **and** non-empty `settings.langsmith_api_key` |
| Otherwise | `obs.langsmith = "skipped"` (no network) |
| Emit API | Soft-pin **`langsmith.Client`**: `create_run` then `update_run` (or equivalent documented Client run lifecycle). Name: `alphaguard.pipeline.run`. `run_type="chain"`. Project: `settings.langsmith_project` |
| Inputs (min) | `run_id`, `event_id`, `ticker`, `mode`, `rag_mode`, `status` |
| Outputs (min) | `action` / `decision` if present (from proposal/decision); else `{}` |
| Success → status | `obs.langsmith = "ok"` **only after** successful create (and update if used) |
| Failure → status | `obs.langsmith = "failed"`; log warning; never raise into pipeline business path |
| Run id persistence | Store string id in `envelope.extras["langsmith_run_id"]` when `ok` (use existing `extras` — avoid ObsStatus schema churn unless needed) |
| Injectability | Adapter accepts optional `client_factory` / mock client for unit tests — **no live LangSmith in default pytest** |
| Phoenix | Leave `phoenix_enabled` stub behavior; docs say **still stub / no real spans** |
| Env | Keep `.env.example` keys; document that `LANGSMITH_TRACING=true` + key enables real emit |
| Smoke | Unchanged fixture path; do not set tracing true in Makefile smoke |
| Optional live mark | Optional `@pytest.mark.langsmith_live` excluded by default `addopts` (alongside kafka/rss exclusions); skip unless `ALPHAGUARD_RUN_LANGSMITH_LIVE=1` |
| Screenshots | **Not** required in DoD |

### Status semantics (freeze)

| Condition | `obs.langsmith` |
|-----------|-----------------|
| Tracing off or empty key | `skipped` |
| Emit succeeded | `ok` |
| Tracing on + key but import/SDK/network/auth error | `failed` |

`ok` **must not** mean “key present.”

---

## Acceptance criteria (Implement must meet)

- [ ] `best_effort_adapters` / LangSmith path emits real Client run/span when configured — not key-presence theater  
- [ ] Tracing off / no key → `skipped`; default smoke green without LangSmith  
- [ ] SDK/network failure → `failed`; pipeline decision unchanged; may `degraded` if already success  
- [ ] `extras["langsmith_run_id"]` set when `ok`  
- [ ] Unit tests with mocks (success / failure / skipped) — default CI never hits LangSmith  
- [ ] Phoenix remains stub (no real Phoenix spans); docs say so  
- [ ] Same-delivery VISION / ARCHITECTURE §13 / README / GETTING_STARTED / INTERVIEW / AGENTS honesty  
- [ ] No MV walkthrough / daily-prep checkbox invent  
- [ ] No secrets committed  

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — Adapter module + injectability

- [ ] **A1.** Add `langsmith` dependency; `uv sync`.  
- [ ] **A2.** Create `src/alphaguard/obs/langsmith_adapter.py`: `emit_pipeline_run(...)` → `(AdapterStatus, run_id | None)` using Client create/update soft pins; catch-all fail-open.  
- [ ] **A3.** Refactor `best_effort_adapters` / `build_obs_status` to accept run context (`run_id`, `event_id`, `ticker`, `mode`, `rag_mode`, `status`, optional proposal/decision summaries) and call the adapter.  
- [ ] **A4.** Update `PipelineService.run` to pass context into `build_obs_status` (after pipeline outcome known). Preserve degraded-on-`failed` behavior.  
- [ ] **A5.** On `ok`, set `extras["langsmith_run_id"]` before final envelope write.

### Phase B — Tests

- [ ] **B1.** Unit: tracing off → `skipped`, no client call.  
- [ ] **B2.** Unit: mock client success → `ok` + `langsmith_run_id` present.  
- [ ] **B3.** Unit: mock client raises → `failed`; helper used by pipeline does not raise.  
- [ ] **B4.** Optional: register `langsmith_live` marker; exclude in `addopts`; one skip-by-default live test.  
- [ ] **B5.** Confirm default `uv run pytest -q` never needs LangSmith network/key.

### Phase C — Docs honesty + stop

- [ ] **C1.** ARCHITECTURE §13: LangSmith = real spans when configured; Phoenix still stub; local envelope mandatory. Fix stale “screenshots not present” if Guide 02 assets exist (honesty Align-in-guide).  
- [ ] **C2.** VISION: note Guide 07 thin LangSmith spans; keep “stubs” language only where still true (Phoenix); **do not** check MV walkthrough/daily-prep.  
- [ ] **C3.** README / GETTING_STARTED / INTERVIEW / AGENTS: reverse “status stubs only” for LangSmith; keep smoke-without-key; no fabricated UI shots.  
- [ ] **C4.** `.env.example` comment: tracing+key enables real emit; empty = skipped.  
- [ ] **C5.** Grep stale “key presence” / “stubs only” contradictions for LangSmith; fix.  
- [ ] **C6.** Stop. No Phoenix real spans, agent-on-consume, Optuna, MV ticks, smoke flip.

### Phase D — Verification

- [ ] **D1.** `uv run pytest -q` green (incl. new obs unit tests).  
- [ ] **D2.** `make smoke` green with default env (LangSmith skipped).  
- [ ] **D3.** Optional operator: with real key, one smoke/replay shows `obs.langsmith=ok` + `langsmith_run_id` — residual if unavailable; not DoD blocker if mocks green.

---

## Verification / Definition of Done

**Done when all are true:**

1. Configured path emits a real LangSmith run (proven by mock tests; optional live).  
2. `ok` never means key-presence alone.  
3. Default smoke / default pytest green without LangSmith key or network.  
4. Fail-open: tracer errors do not destroy valid gate decisions.  
5. Docs honesty updated same delivery; Phoenix stub called out; MV human boxes untouched.  

**Explicitly not required:**

- Phoenix real spans  
- LangSmith UI screenshots in `docs/assets/`  
- Smoke requires tracing  
- Agent-on-consume  
- Live-Ollama eval rates  
- Ticking VISION walkthrough / daily-prep  

**Suggested verification commands:**

```bash
# From alphaguard/
uv run pytest -q
make smoke

# Optional live (operator machine with key):
# export LANGSMITH_TRACING=true LANGSMITH_API_KEY=... LANGSMITH_PROJECT=alphaguard
# make smoke   # expect obs.langsmith=ok and extras.langsmith_run_id
# ALPHAGUARD_RUN_LANGSMITH_LIVE=1 uv run pytest -m langsmith_live -q
```

---

## Blast radius and risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Smoke/CI requires LangSmith | Clone path breaks; secret leakage pressure | Default tracing false; mocks only in CI |
| Theater continues (`ok` without emit) | Interview trust | DoD + tests assert client called |
| Adapter exceptions abort pipeline | False `error` runs | Broad catch in adapter; pipeline unchanged |
| Logging API keys | Security | Log project/status only; never key |
| Phoenix still `ok` without spans | Mild honesty hole | Docs: Phoenix stub; optional follow-on guide |
| File-size / second orchestrator | Maintainability | Thin `langsmith_adapter.py`; PipelineService stays façade |

---

## Edge-case handling (must appear in Implement or tests)

| Case | Required behavior |
|------|-------------------|
| `LANGSMITH_TRACING=false` | `skipped`; no Client constructed |
| Empty / whitespace API key | Treat as skipped or failed-closed-to-skipped (prefer **skipped**); no network |
| `langsmith` package missing while tracing on | `failed`; warn; fail-open |
| Network / 401 / timeout from Client | `failed`; fail-open |
| Pipeline already `error` | Still attempt emit optional; prefer always attempt with status=`error` for honesty; must not raise |
| Success + langsmith `failed` | Existing rule: envelope `degraded` OK |
| Success + langsmith `ok` | `success`; extras include `langsmith_run_id` |

---

## Out of scope (stop list)

- Implement in this Write stage  
- Real Phoenix spans  
- Agent-on-consume / Kafka consumer Agent 1→2  
- Requiring LangSmith for smoke or default pytest  
- Fabricated LangSmith UI screenshots  
- Optuna / W&B / Option B smoke flip  
- Inventing VISION MV walkthrough / daily-prep checkmarks  
- Brokerage / Lowd Capital / second LLM auditor  

---

## Honest readiness

- **Write-dev-guide DoD:** met when this file exists with steps, soft pins, DoD, blast radius, edge cases.  
- **Next stage:** Ready-check before code (hub pre-authorized per pass 123).  
- **Not started:** any LangSmith SDK wiring code.

## QUALITY self-check (§5)

- [x] Executable steps + DoD + verification commands  
- [x] Edge cases + blast radius explicit  
- [x] Locks mirrored (LangSmith only; Phoenix stub; fixture smoke; MV human-only)  
- [x] No implementation in this stage  
- [x] Docs honesty + fail-open called out  
