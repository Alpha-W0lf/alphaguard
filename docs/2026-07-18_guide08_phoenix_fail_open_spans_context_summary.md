# Context: Guide 08 — Phoenix real fail-open spans

**Date:** 2026-07-18  
**Repos:** `alphaguard`  
**Status:** Draft (Gather Met) — ready for Write-dev-guide after soft pins  
**Mode last used:** spoke (Gather pass 151)  
**Stage:** Gather context  
**Role lens:** Senior AI eng (LLMOps honesty / fail-open telemetry)  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_gather_guide08_phoenix_pass151_handoff.md`  
**Hub:** `second_brain/docs/2026-07-18_prioritize_hub_pass151.md` (Guide 08 = Phoenix thin slice)

## Problem

Guide 07 closed LangSmith status theater: `obs.langsmith=ok` now means a real Client run was emitted. Phoenix still has the **same honesty gap** Guide 07 left deferred:

In `obs/summary.py` `best_effort_adapters`, when `settings.phoenix_enabled` is true, the adapter sets `phoenix = "ok"` inside a try/except **without calling any Phoenix / OpenTelemetry API**. That is status theater — interviewers and clone reviewers can be misled into thinking dual-backend LLMOps is wired.

VISION / ARCHITECTURE / README already call this out honestly (“Phoenix status stub”). Guide 08 replaces the stub with a **thin real fail-open emit**, mirroring Guide 07’s contract shape, without flipping default smoke or requiring a Phoenix collector for CI.

## Acceptance criteria

- [ ] When Phoenix is configured (see soft pins), adapter emits **at least one real OpenTelemetry / OpenInference span** to a Phoenix collector path — not flag-presence theater  
- [ ] `obs.phoenix=ok` **only after** successful emit (create + end/export); else `skipped` (off) or `failed` (import/SDK/network/collector)  
- [ ] Default smoke / default pytest: `PHOENIX_ENABLED=false` → `skipped`; **never** requires Phoenix UI, collector, or API key  
- [ ] Fail-open relative to gate: tracer errors must **not** flip `approve|reject`; existing success + adapter `failed` → envelope `degraded` stays  
- [ ] Local run summary remains mandatory (`artifacts/runs/*.json`) regardless of Phoenix  
- [ ] Unit tests with injectable tracer/exporter mocks (success / failure / skipped); optional live mark excluded by default `addopts`  
- [ ] Same-delivery docs honesty (VISION / ARCHITECTURE §13 / README / GETTING_STARTED / INTERVIEW / AGENTS / `.env.example`) — **no** invent VISION Interview-prep checkbox ticks  
- [ ] No secrets in git; no fabricated Phoenix UI screenshots required in DoD  

## In scope

- Thin Phoenix adapter under `obs/` (mirror `langsmith_adapter.py`)  
- Wire `best_effort_adapters` / `build_obs_status` / pipeline extras (optional span/trace id)  
- Config / `.env.example` honesty for enable + collector endpoint  
- Mocked unit tests + optional `phoenix_live` marker  
- Docs honesty for “real when configured; stub language removed”  

## Out of scope

- Agent-on-consume / 24/7 RSS reliability  
- Requiring Phoenix for smoke or default CI  
- Full OpenInference auto-instrument of LangGraph / LangChain / Ollama (global tracer sprawl)  
- Cloud Phoenix SaaS as a hard DoD (local collector optional for live probe only)  
- Fabricated Phoenix UI screenshots in `docs/assets/`  
- Optuna / W&B / Option B smoke flip / brokerage / Lowd Capital / second LLM auditor  
- Inventing VISION Interview-prep walkthrough / daily hand-coding ticks  
- Expanding Guide 08 into unrelated portfolio work  

## Prior art (paths only)

| Path | Why it matters |
|------|----------------|
| `src/alphaguard/obs/summary.py` | Phoenix stub (`ok` when enabled, no SDK) |
| `src/alphaguard/obs/langsmith_adapter.py` | **Pattern to mirror** — thin emit, injectability, fail-open |
| `tests/test_langsmith_obs.py` | Test shape: skipped / ok+id / failed / pipeline degraded |
| `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md` | Guide 07 locked pins + DoD template |
| `docs/ARCHITECTURE.md` §7.7, §7.8, §10, **§13** | Envelope + fail-open + current Phoenix stub truth |
| `docs/VISION.md` | LLMOps; Phoenix still stub in MV row |
| `src/alphaguard/config.py` | `phoenix_enabled: bool` only today |
| `.env.example` | `PHOENIX_ENABLED=false` + stub comment |
| `src/alphaguard/pipeline/service.py` | Already degrades on `obs.phoenix == "failed"` |
| `src/alphaguard/contracts/envelope.py` | `ObsStatus.phoenix`; `extras` for ids |
| `docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md` | Post–07 inventory; Phoenix deferred |
| `pyproject.toml` | No Phoenix dep yet; `langsmith_live` marker pattern |
| Arize docs: `phoenix.otel.register` + manual chain span (`arize-phoenix-otel`) | Candidate thin emit API |

## Current stub behavior (evidence)

```53:62:src/alphaguard/obs/summary.py
    phoenix: AdapterStatus = "skipped"
    if settings.phoenix_enabled:
        try:
            # Stub: no real Phoenix spans in Guide 07 — status only.
            phoenix = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("phoenix adapter failed open: %s", exc)
            phoenix = "failed"
    else:
        phoenix = "skipped"
```

- Config: `Settings.phoenix_enabled` ← env `PHOENIX_ENABLED` (default `false`).  
- No `arize-phoenix` / `arize-phoenix-otel` in `pyproject.toml` dependencies.  
- Pipeline already treats Phoenix `failed` like LangSmith for `degraded` (no gate flip).

## Risks and blast radius

| Risk | Angle | Mitigation |
|------|-------|------------|
| Smoke/CI requires Phoenix collector | Clone path breaks; secret/env pressure | Default `PHOENIX_ENABLED=false`; mocks only in CI |
| Theater continues (`ok` without export) | Interview trust | DoD + tests assert span/export path invoked; `ok` only after success |
| Global `register()` side effects | Other tests / LangSmith / OTEL global provider pollution | Prefer inject factory; register only when enabled; keep `auto_instrument=False` |
| Heavy dep (`arize-phoenix` full UI) | Install size, 16GB RAM story | Prefer **`arize-phoenix-otel` only** (soft pin) |
| Adapter exceptions abort pipeline | False `error` runs | Broad catch; never raise into business path |
| Dual-backend “maturity” overclaim | Docs drift | Same-delivery honesty; still “thin one span,” not full LLM tree |
| Batch exporter drops span before process exit | Flaky live probe | Soft-pin `batch=False` / SimpleSpanProcessor + `force_flush` before `ok` |

## Edge cases

| Case | Required behavior |
|------|-------------------|
| `PHOENIX_ENABLED=false` | `skipped`; no tracer/register |
| Enabled but package missing | `failed`; warn; fail-open |
| Enabled + collector unreachable / timeout | `failed`; fail-open |
| Enabled + mock exporter success | `ok`; optional `extras.phoenix_span_id` / `trace_id` |
| Pipeline already `error` | Still may attempt emit with status=`error`; must not raise |
| Success + phoenix `failed` | Envelope `degraded` (existing rule) |
| LangSmith ok + Phoenix skipped | Independent adapters; no coupling |
| Whitespace-only endpoint override (if added) | Prefer treat as default endpoint or `skipped`/`failed` — pin in Write |

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking? |
|---------|----------------|-----------|
| Exact soft-pin API for “success” (span end vs `force_flush` vs exporter callback) | Write-dev-guide soft pin + Implement Adjust if SDK differs | Soft — not blocking Gather |
| Default collector URL for live probe (`http://localhost:6006/v1/traces` HTTP vs gRPC `:4317`) | Soft-pin HTTP protobuf to Phoenix UI default; document in `.env.example` | Soft |
| Whether `extras` key is `phoenix_span_id`, `phoenix_trace_id`, or both | Mirror LangSmith: one id string preferred; pin in Write | Soft |
| Live Phoenix UI screenshot for portfolio | Explicitly **out** of DoD (same as Guide 07 LS UI) | No |

## Recommended approach

Mirror Guide 07 exactly in shape:

1. **New thin module** `src/alphaguard/obs/phoenix_adapter.py` with `emit_pipeline_span(...) → (AdapterStatus, span_id | None)` — never raises.  
2. **Dependency soft-pin:** add `arize-phoenix-otel` (not full `arize-phoenix` app package). Import inside try/except.  
3. **When to attempt:** `settings.phoenix_enabled is True`; else `skipped`.  
4. **Emit soft-pin:** `phoenix.otel.register(project_name=..., endpoint=..., protocol="http/protobuf", batch=False, auto_instrument=False)` then one manual span named `alphaguard.pipeline.run` with OpenInference kind **chain**, min attributes = same inputs/outputs as LangSmith (`run_id`, `event_id`, `ticker`, `mode`, `rag_mode`, `status` + action/decision).  
5. **`ok` only after** span ends and export flush succeeds (or injectable exporter confirms).  
6. **Injectability:** optional `tracer_factory` / exporter mock for unit tests — default pytest never hits network.  
7. **Optional** `@pytest.mark.phoenix_live` + `ALPHAGUARD_RUN_PHOENIX_LIVE=1`, excluded in `addopts`.  
8. **Docs / env:** reverse “status stub” for Phoenix; keep smoke-without-Phoenix; record optional `PHOENIX_COLLECTOR_ENDPOINT` / project name in `.env.example`.  
9. **Do not** auto-instrument LangChain/LangGraph in this guide.

## Open decisions (human)

### Decision: Package and emit surface for Guide 08

- **Plain title:** Which Phoenix dependency and emit API should Guide 08 lock?
- **In plain terms:** We need a real span when Phoenix is on, without dragging a heavy UI server into every clone install, and without auto-instrumenting the whole stack.
- **Options:**  
  - **A** — `arize-phoenix-otel` + `phoenix.otel.register` + one manual chain span (recommended)  
  - **B** — Full `arize-phoenix` package (UI + more) + same OTEL path  
  - **C** — Raw OpenTelemetry SDK exporters only (no Phoenix helper)
- **Recommendation:** **A**
- **Reasoning:** Matches VISION “Phoenix local fallback,” mirrors Guide 07’s thin-adapter discipline, keeps install lighter than full Phoenix, and is the documented Arize path for manual spans. Option C reinvent wrappers Phoenix already ships.
- **Tradeoffs:** A still needs a running collector for live `ok` (or mocks in CI). B adds weight. C is more code and easier to get exporter defaults wrong.
- **Needs from you:** Say “lock A” / “prefer B” / “prefer C”, or park until Refine.

### Decision: Config gate for attempting emit

- **Plain title:** What env flags must be set before we attempt a Phoenix span?
- **In plain terms:** Today only `PHOENIX_ENABLED` exists. Collectors usually need an endpoint too.
- **Options:**  
  - **A** — `PHOENIX_ENABLED=true` alone; use Phoenix OTEL defaults (`localhost:6006` / documented default)  
  - **B** — `PHOENIX_ENABLED=true` **and** non-empty `PHOENIX_COLLECTOR_ENDPOINT` (else `skipped`)  
  - **C** — Always attempt when enabled; empty endpoint → `failed` (not skipped)
- **Recommendation:** **A** with documented optional `PHOENIX_COLLECTOR_ENDPOINT` / `PHOENIX_PROJECT_NAME` overrides (parallel to LangSmith project override). Live probe documents “collector must be up.”
- **Reasoning:** Closest to current `.env.example` one-flag model; avoids inventing a second required secret for local fallback. Unreachable collector correctly becomes `failed` fail-open.
- **Tradeoffs:** A can surprise operators who flip the flag without starting Phoenix (honest `failed` + degraded). B is stricter and reduces accidental network attempts.
- **Needs from you:** Lock A or B (C not recommended).

### Decision: Persist Phoenix id in envelope extras?

- **Plain title:** Should a successful Phoenix emit store an id in `envelope.extras` like LangSmith?
- **Options:** **A** store `extras.phoenix_span_id` (or trace id) on `ok` · **B** status-only (no extras key)
- **Recommendation:** **A** — one string id (prefer span id; document which).
- **Reasoning:** Symmetry with Guide 07 (`langsmith_run_id`); easier interview proof and live-probe asserts.
- **Tradeoffs:** Tiny schema surface in `extras` (already free-form). B is smaller but weaker proof.
- **Needs from you:** Lock A or B.

## Evidence opened this pass

- Handoff: `second_brain/docs/2026-07-18_spoke_alphaguard_gather_guide08_phoenix_pass151_handoff.md`  
- Hub prioritize: `second_brain/docs/2026-07-18_prioritize_hub_pass151.md`  
- `docs/VISION.md`, `docs/ARCHITECTURE.md` (§7.7–7.8, §13)  
- Guide 07: `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
- Inventory: `docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md`  
- Code: `obs/summary.py`, `obs/langsmith_adapter.py`, `config.py`, `pipeline/service.py`, `contracts/envelope.py`, `tests/test_langsmith_obs.py`, `.env.example`, `pyproject.toml`  
- Docs: README Phoenix stub rows; AGENTS locked stack  
- External: Arize Phoenix `phoenix.otel.register` + manual chain span (`arize-phoenix-otel`) via Context7 / public docs  

## Honest readiness

- **Gather DoD:** Met — problem, AC, in/out, prior art, risks, edges, unknowns, approach, open decisions with recommendations.  
- **Ready for Write-dev-guide?** **Yes** — soft pins above are enough to author a Guide 08 thin guide mirroring Guide 07; human can Refine first to lock A/B decisions if desired.  
- **Not ready for Implement** until Write + Ready-check.  
- **Will not** tick VISION Interview-prep boxes from any agent stage.

## QUALITY self-check (§5)

- [x] Assumptions listed as soft pins / open decisions — not silently locked  
- [x] Did not rush; stub + Guide 07 + Phoenix OTEL evidence cited  
- [x] Declare Mode/Stage before act (spoke Gather)  
- [x] Edge cases + blast radius (≥2 angles: CI/clone, global OTEL, docs honesty)  
- [x] Findings written to this artifact + handoff Results  
- [x] Spoke stayed in Guide 08 Phoenix slice; no Implement  
- [x] Open decisions surfaced with recommendation + reasoning + tradeoffs  
- [x] Verification plan clear for later Implement (mirror Guide 07 tests + smoke)  
