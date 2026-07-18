# Dev Guide 08 — Phoenix real fail-open spans (thin)

**Date:** 2026-07-18  
**Repo:** `alphaguard`  
**Work item:** Guide 08 — replace Phoenix envelope status theater with real fail-open OTEL span emit  
**Stage that authored this:** Write-dev-guide (pass 152); Ready-check (9.0); Implement (`e5aad97`); Review (`a60a417`); Align-docs (pass 152)  
**Status:** **Aligned / slice closed** (pass 152) — Review shippable; docs match shipped reality; Phoenix real fail-open; fixture smoke default; Interview-prep boxes untouched

**Context SSOT:** `alphaguard/docs/2026-07-18_guide08_phoenix_fail_open_spans_context_summary.md`  
**Hub:** `second_brain/docs/2026-07-18_prioritize_hub_pass152.md`  
**Write handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_write_guide08_phoenix_pass152_handoff.md`  
**Prerequisite:** Guides 01–07 shippable (Guide 07 LangSmith real fail-open). Local run envelope real (`obs/summary.py`). Default smoke remains fixture / Kafka-down. **Guide 08 shipped:** Phoenix = real fail-open OTEL chain spans when `PHOENIX_ENABLED` (not stub).

**Human locks (pass 152 — do not reopen):**

| Lock | Value |
|------|--------|
| Package / emit | **A** — `arize-phoenix-otel` + `phoenix.otel.register` + **one** manual chain span |
| Config gate | **A** — `PHOENIX_ENABLED=true` alone (optional endpoint / project overrides) |
| Extras id | **A** — `extras.phoenix_span_id` on success |
| Scope | **Phoenix real fail-open spans only** — no auto-instrument sprawl |
| Smoke | Fixture / Kafka-down default; **never** requires Phoenix collector / UI / API key |
| Interview-prep VISION boxes | **Human-only** — do not invent ticks |
| Agent-on-consume / Optuna / brokerage / Lowd | **Out** |

---

## Objective

Close the remaining LLMOps honesty gap after Guide 07: today `best_effort_adapters` sets `obs.phoenix=ok` when `PHOENIX_ENABLED` is true **without emitting any OpenTelemetry / Phoenix span**. Guide 08 makes `ok` mean **at least one real chain span was successfully created, ended, and flushed/exported** (or records honest `skipped`/`failed`), while keeping **local run summary mandatory** and **fail-open** relative to pipeline approve/reject.

**Success signal:** Unit tests prove (1) Phoenix off → `skipped`, (2) mocked successful emit → `ok` + `extras.phoenix_span_id`, (3) mocked SDK/network/collector failure → `failed` and pipeline status may be `degraded` but decision unchanged; `make smoke` with default env (`PHOENIX_ENABLED=false`) still green fixture path.

---

## Learning notes (new for this guide)

1. **Fail-open telemetry** — Observability must not rewrite business outcomes. Tracer/collector down → envelope `failed` / run `degraded`; gate decision stays valid.  
2. **Status field ≠ span** — Setting `ok` from `PHOENIX_ENABLED` alone is theater. Interviewers ask what was exported.  
3. **Local envelope remains SSOT for clone path** — Phoenix is optional enrichment when configured.  
4. **Thin manual span vs auto-instrument** — One OpenInference **chain** span proves honesty without global LangGraph/LangChain instrumentor side effects.  
5. **Flush before claiming success** — With SimpleSpanProcessor / `batch=False`, still call `force_flush` (or equivalent) before returning `ok` so process exit does not drop the span.

---

## References (paths only)

- `alphaguard/docs/2026-07-18_guide08_phoenix_fail_open_spans_context_summary.md`
- `alphaguard/docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md` (mirror shape)
- `alphaguard/docs/ARCHITECTURE.md` (§7.7 envelope, §10 tracer failure, **§13 Observability**)
- `alphaguard/docs/VISION.md` (LLMOps; Interview-prep human boxes)
- `alphaguard/src/alphaguard/obs/summary.py` (Phoenix stub theater)
- `alphaguard/src/alphaguard/obs/langsmith_adapter.py` (pattern to mirror)
- `alphaguard/src/alphaguard/pipeline/service.py` (`build_obs_status`, degraded-on-adapter-failed)
- `alphaguard/src/alphaguard/contracts/envelope.py` (`ObsStatus`, `extras`)
- `alphaguard/src/alphaguard/config.py` (`phoenix_enabled`)
- `alphaguard/.env.example` (`PHOENIX_ENABLED`)
- `alphaguard/tests/test_langsmith_obs.py` (test shape to mirror)
- `alphaguard/{README,GETTING_STARTED,INTERVIEW,AGENTS}.md`
- `alphaguard/docs/assets/README.md` (local-envelope screenshot honesty)
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`
- External: Arize `phoenix.otel.register` + manual chain span (`arize-phoenix-otel`)

---

## Architecture constraints (binding)

1. **Phoenix thin adapter only.** No LangChain/LangGraph/Ollama auto-instrument. No agent-on-consume. No smoke default flip. No Optuna/W&B.  
2. **Local envelope remains mandatory** — write `artifacts/runs/<run_id>.json` regardless of Phoenix.  
3. **Fail-open (DF-6 / §13):** SDK import error, register failure, timeout, or collector/network failure → `obs.phoenix=failed`; must **not** flip `approve|reject` or force pipeline `error` solely due to tracer. Existing `degraded` when success+adapter failed stays OK.  
4. **Smoke never requires Phoenix** — default `.env` / CI: `PHOENIX_ENABLED=false` → `skipped`; smoke green.  
5. **No secrets in git** — never commit Phoenix/cloud API keys; never print full keys in logs.  
6. Prefer ≤300 lines/file (hard max 400). Prefer new thin module `obs/phoenix_adapter.py` + slim changes to `summary.py` / `pipeline/service.py` / `config.py`.  
7. Docs honesty same delivery; **never** tick VISION Interview-prep walkthrough / daily hand-coding boxes.  
8. Do **not** fabricate Phoenix UI screenshots. Optional real UI capture is **out** of DoD (envelope + unit mocks suffice).  
9. **LangSmith Guide 07 path stays** — independent adapters; do not regress LangSmith emit.

---

## Soft pins (locked — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Dependency | Add **`arize-phoenix-otel`** to project deps (`pyproject.toml` / `uv sync`). **Do not** add full `arize-phoenix` UI package for this guide. Import inside adapter try/except so missing install → `failed` when enabled |
| When to attempt emit | `settings.phoenix_enabled is True` (`PHOENIX_ENABLED=true`) |
| Otherwise | `obs.phoenix = "skipped"` (no register / no network) |
| Optional overrides | Document `PHOENIX_COLLECTOR_ENDPOINT` (default Phoenix HTTP traces URL) and `PHOENIX_PROJECT_NAME` (default `alphaguard`) in Settings + `.env.example`. Empty/whitespace endpoint → use library/default localhost HTTP path — **do not** require endpoint for attempt (Tom lock A) |
| Emit API | Soft-pin **`phoenix.otel.register`**: `project_name=...`, `endpoint=...` when override set, `protocol="http/protobuf"`, `batch=False`, **`auto_instrument=False`**. Then one manual span |
| Span | Name: `alphaguard.pipeline.run`. OpenInference span kind: **chain**. Min attributes / I/O: `run_id`, `event_id`, `ticker`, `mode`, `rag_mode`, `status`; outputs `action` / `decision` when present |
| Success → status | `obs.phoenix = "ok"` **only after** span ends **and** `force_flush` (or equivalent exporter confirm) succeeds |
| Failure → status | `obs.phoenix = "failed"`; log warning; never raise into pipeline business path |
| Span id persistence | Store string id in `envelope.extras["phoenix_span_id"]` when `ok` (hex/span context string from the ended span — prefer span id; document in adapter docstring). Use existing `extras` — avoid `ObsStatus` schema churn |
| Injectability | Adapter accepts optional `tracer_factory` / provider factory for unit tests — **no live Phoenix collector in default pytest** |
| LangSmith | Leave Guide 07 path unchanged |
| Env | Update `.env.example`: `PHOENIX_ENABLED=false` enables real emit when true; comment optional collector/project; reverse “status stub” wording |
| Smoke | Unchanged fixture path; do **not** set `PHOENIX_ENABLED=true` in Makefile smoke |
| Optional live mark | `@pytest.mark.phoenix_live` excluded by default `addopts` (with kafka/rss/langsmith exclusions); skip unless `ALPHAGUARD_RUN_PHOENIX_LIVE=1` |
| Screenshots | **Not** required in DoD |
| Soft Adjust allowed | If `register` / span attribute API differs slightly by package version, Implement may Soft Adjust **within** one manual chain span + fail-open + flush-before-ok — do not expand to auto-instrument |

### Status semantics (freeze)

| Condition | `obs.phoenix` |
|-----------|---------------|
| `PHOENIX_ENABLED=false` / not set | `skipped` |
| Emit + flush succeeded | `ok` |
| Enabled but import/SDK/register/network/collector/flush error | `failed` |

`ok` **must not** mean “flag present.”

### Default collector (operator docs)

For live probe / optional operator path, document default HTTP traces endpoint:

`http://localhost:6006/v1/traces`

(Phoenix UI default; `protocol="http/protobuf"`). Operator must have a Phoenix collector/UI listening — **not** a smoke/CI requirement.

---

## Acceptance criteria (Implement must meet)

- [x] `best_effort_adapters` / Phoenix path emits a real OTEL/OpenInference chain span when `PHOENIX_ENABLED=true` — not flag-presence theater  
- [x] Phoenix off → `skipped`; default smoke green without Phoenix collector  
- [x] SDK/network/collector/flush failure → `failed`; pipeline decision unchanged; may `degraded` if already success  
- [x] `extras["phoenix_span_id"]` set when `ok`  
- [x] Unit tests with mocks (success / failure / skipped) — default CI never hits Phoenix  
- [x] Optional `phoenix_live` marker excluded by default  
- [x] LangSmith Guide 07 behavior unchanged  
- [x] Same-delivery VISION / ARCHITECTURE §13 / README / GETTING_STARTED / INTERVIEW / AGENTS / `.env.example` honesty (reverse Phoenix “status stub” where no longer true)  
- [x] No Interview-prep VISION checkbox invent  
- [x] No secrets committed  

---

## Ordered step checklist

Implement evidence: `tests/test_phoenix_obs.py`; Soft Adjust (`arize-phoenix-otel==0.16.1`): keyword-only `register(..., set_global_tracer_provider=False, verbose=False)`; `openinference_span_kind="chain"`; `force_flush` before `ok`. `uv run pytest -q` → 105 passed, 6 deselected; `make smoke` → `obs.phoenix=skipped`.

### Phase A — Adapter module + injectability

- [x] **A1.** Add `arize-phoenix-otel` dependency; `uv sync`.  
- [x] **A2.** Create `src/alphaguard/obs/phoenix_adapter.py`: `emit_pipeline_span(...)` → `(AdapterStatus, span_id | None)` using register + one chain span + `force_flush`; catch-all fail-open.  
- [x] **A3.** Extend Settings if needed: optional `phoenix_collector_endpoint`, `phoenix_project_name` (defaults documented); keep `phoenix_enabled` as sole attempt gate.  
- [x] **A4.** Refactor `best_effort_adapters` / `build_obs_status` to call Phoenix adapter (pass same run context as LangSmith). Return phoenix status + span id alongside LangSmith.  
- [x] **A5.** Update `PipelineService.run` to set `extras["phoenix_span_id"]` when `ok`. Preserve degraded-on-`failed` for either adapter.  
- [x] **A6.** Prefer ≤300 lines/file; do not grow `summary.py` into a second orchestrator.

### Phase B — Tests

- [x] **B1.** Unit: `phoenix_enabled=False` → `skipped`, no register/tracer call.  
- [x] **B2.** Unit: mock tracer/provider success → `ok` + `phoenix_span_id` present.  
- [x] **B3.** Unit: mock raises / flush fails → `failed`; pipeline helper does not raise.  
- [x] **B4.** Pipeline integration-style (mirror LangSmith): success + phoenix failed → `degraded`, decision unchanged.  
- [x] **B5.** Register `phoenix_live` marker; exclude in `addopts`; one skip-by-default live test.  
- [x] **B6.** Confirm default `uv run pytest -q` never needs Phoenix network/collector.  
- [x] **B7.** Confirm existing LangSmith unit tests still green (no regress).

### Phase C — Docs honesty + stop

- [x] **C1.** ARCHITECTURE §7.8 / §13: Phoenix = real fail-open spans when enabled; local envelope mandatory; LangSmith unchanged.  
- [x] **C2.** VISION: note Guide 08 thin Phoenix spans; remove “Phoenix still stub” where false; **do not** check Interview-prep boxes.  
- [x] **C3.** README / GETTING_STARTED / INTERVIEW / AGENTS: reverse Phoenix “status stub”; keep smoke-without-Phoenix; no fabricated UI shots.  
- [x] **C4.** `.env.example`: `PHOENIX_ENABLED=true` enables real emit; optional collector/project; default smoke false.  
- [x] **C5.** Grep stale “Phoenix stub” / “status stub” / “no real Phoenix spans” contradictions; fix.  
- [x] **C6.** Stop. No auto-instrument, agent-on-consume, Optuna, Interview-prep ticks, smoke flip.

### Phase D — Verification

- [x] **D1.** `uv run pytest -q` green (incl. new Phoenix obs unit tests; LangSmith tests still pass).  
- [x] **D2.** `make smoke` green with default env (Phoenix skipped).  
- [ ] **D3.** Optional operator: Phoenix UI/collector up + `PHOENIX_ENABLED=true` → one smoke/replay shows `obs.phoenix=ok` + `phoenix_span_id` — residual if unavailable; not DoD blocker if mocks green.

---

## Verification / Definition of Done

**Done when all are true:**

1. Configured path emits a real Phoenix/OTEL chain span (proven by mock tests; optional live).  
2. `ok` never means `PHOENIX_ENABLED` alone.  
3. Default smoke / default pytest green without Phoenix collector or network.  
4. Fail-open: tracer errors do not destroy valid gate decisions.  
5. `extras.phoenix_span_id` present on `ok`.  
6. Docs honesty updated same delivery; Interview-prep human boxes untouched.  
7. LangSmith Guide 07 path still works.

**Explicitly not required:**

- Full OpenInference auto-instrument of LangGraph / LangChain / Ollama  
- Phoenix UI screenshots in `docs/assets/`  
- Smoke requires Phoenix  
- Agent-on-consume  
- Live-Ollama eval rates  
- Ticking VISION Interview-prep walkthrough / daily hand-coding  
- Full `arize-phoenix` UI package as a runtime dependency  

**Suggested verification commands:**

```bash
# From alphaguard/
uv run pytest -q
make smoke

# Optional live (operator machine with Phoenix collector on :6006):
# export PHOENIX_ENABLED=true
# optional: export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
# optional: export PHOENIX_PROJECT_NAME=alphaguard
# make smoke   # expect obs.phoenix=ok and extras.phoenix_span_id
# ALPHAGUARD_RUN_PHOENIX_LIVE=1 uv run pytest -m phoenix_live -q
```

---

## Blast radius and risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Smoke/CI requires Phoenix collector | Clone path breaks | Default `PHOENIX_ENABLED=false`; mocks only in CI |
| Theater continues (`ok` without export) | Interview trust | DoD + tests assert span/flush path; `ok` only after success |
| Global `register()` pollutes other tests | Flaky OTEL / LangSmith interaction | Inject factory in tests; register only when enabled; `auto_instrument=False` |
| Batch exporter drops span on exit | Flaky live probe | `batch=False` + `force_flush` before `ok` |
| Heavy full `arize-phoenix` dep | Install / RAM story | Locked: `arize-phoenix-otel` only |
| Adapter exceptions abort pipeline | False `error` runs | Broad catch; never raise |
| Docs still say “Phoenix stub” | Honesty regression | Phase C grep + same-delivery Align-in-guide |
| File-size / second orchestrator | Maintainability | Thin `phoenix_adapter.py`; PipelineService stays façade |

---

## Edge-case handling (must appear in Implement or tests)

| Case | Required behavior |
|------|-------------------|
| `PHOENIX_ENABLED=false` | `skipped`; no `register` / tracer |
| Enabled + `arize-phoenix-otel` missing | `failed`; warn; fail-open |
| Enabled + collector unreachable / timeout | `failed`; fail-open |
| Enabled + register ok but `force_flush` fails | `failed`; fail-open |
| Empty / whitespace optional endpoint override | Use documented default HTTP traces URL; still attempt (lock A) |
| Pipeline already `error` | Still attempt emit with status=`error` for honesty; must not raise |
| Success + phoenix `failed` | Existing rule: envelope `degraded` OK |
| Success + phoenix `ok` | `success`; extras include `phoenix_span_id` |
| LangSmith ok + Phoenix skipped | Independent; both fields correct |
| LangSmith failed + Phoenix ok | `degraded` (either adapter failed); decision unchanged |

---

## Out of scope (stop list)

- Implement in this Write stage  
- Full auto-instrument of LangChain / LangGraph / Ollama  
- Agent-on-consume / Kafka consumer Agent 1→2  
- Requiring Phoenix for smoke or default pytest  
- Fabricated Phoenix UI screenshots  
- Adding full `arize-phoenix` UI package as required dep  
- Optuna / W&B / Option B smoke flip  
- Inventing VISION Interview-prep checkmarks  
- Brokerage / Lowd Capital / second LLM auditor  
- Regressing or rewriting Guide 07 LangSmith adapter  

---

## Honest readiness

- **Write-dev-guide / Ready-check:** Met (READY 9.0/10).  
- **Implement DoD:** **Met** (`e5aad97`).  
- **Review:** **Shippable as-is** — `docs/2026-07-18_guide08_phoenix_fail_open_review.md` (`a60a417`).  
- **Align-docs:** **Met** (pass 152) — status honesty stamped; Interview-prep boxes untouched.  
- **Residual (non-blocking):** D3 live Phoenix collector probe; OTEL `force_flush` True-on-dead-collector quirk.  
- **Slice closed.** Hub Prioritize for any next AlphaGuard work — **do not self-start**.  
- **Will not** tick Interview-prep VISION boxes from any agent stage.

## QUALITY self-check (§5)

- [x] Assumptions eliminated via Tom locks A/A/A (package, gate, extras id)  
- [x] Steps, DoD, blast radius, edge cases present  
- [x] No code implemented this stage  
- [x] Spoke stayed in Guide 08 Phoenix slice  
- [x] Mirror of Guide 07 shape for later Implement agent  
