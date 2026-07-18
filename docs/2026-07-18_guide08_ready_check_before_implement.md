# Ready check before code — AlphaGuard Guide 08 (pass 152)

**Status:** Ready-check complete → **READY 9.0/10** — Implement authorized and **Met** (`e5aad97`); Review shippable (`a60a417`); **Align Met** (pass 152) — slice closed
**Guide:** `alphaguard/docs/dev_guides/2026-07-18_dev_guide_08_phoenix_fail_open_spans.md`  
**Context:** `alphaguard/docs/2026-07-18_guide08_phoenix_fail_open_spans_context_summary.md`  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_ready_guide08_phoenix_pass152_handoff.md`  
**Locks:** A/A/A (Tom pass 152)  
**Persistent spoke:** `0a88890e-8c9d-4101-b019-8754f212607d`

## Declare

Zoom-out Implement readiness. **No coding.** Locks A/A/A unchanged. Implement still needs hub/human authorize (handoff: standing authorize if Ready ≥8 — this stage still does **not** Implement).

## Checklist

| Question | Verdict |
|----------|---------|
| Context + guide aligned? | **Yes** — Guide 08 = Phoenix real fail-open spans only; `arize-phoenix-otel` + one manual chain span; `PHOENIX_ENABLED` gate; `extras.phoenix_span_id`; fixture smoke; Interview-prep human-only; matches Gather context + Tom locks |
| Current code matches problem statement? | **Yes** — `obs/summary.py` still sets `phoenix="ok"` when `phoenix_enabled` with **no SDK emit** (stub theater); `PipelineService` already maps success + adapter `failed` → `degraded` for Phoenix; `extras` exists; LangSmith Guide 07 path present as mirror |
| Soft pins unambiguous? | **Yes** — dep `arize-phoenix-otel`; attempt when `phoenix_enabled`; `phoenix.otel.register` + one chain span + `force_flush`; `extras["phoenix_span_id"]`; injectable tracer/provider; optional `phoenix_live` excluded by default; Soft Adjust allowed within emit surface |
| Blast radius / rollback clear? | **Yes** — touch `obs/phoenix_adapter.py` (new), `obs/summary.py`, slim `pipeline/service.py` / `config.py`, `pyproject.toml` (+ pytest marker), docs honesty, tests. Rollback = revert those + drop dep; default smoke path unchanged |
| Edge cases planned? | **Yes** — off → `skipped`; missing package / network / flush fail → `failed` fail-open; success+failed → `degraded`; empty optional endpoint → default URL; error runs may still attempt; LangSmith independence; never flip approve/reject |
| Docs honesty / Interview-prep boxes? | **Yes** — Phase C same-delivery honesty; walkthrough/daily-prep **not** to be checked; Phoenix UI screenshots **out** of DoD |
| Refinements still required before Implement? | **No material** — residuals below are Implement Soft Adjust / operator optional, not a Refine-dev-guide gate |

## Soft residuals (non-blocking)

| Item | Note |
|------|------|
| Exact `register` / span attribute / `force_flush` kwargs | Soft Adjust at Implement against installed `arize-phoenix-otel` docs; stay within one chain span + fail-open + flush-before-ok |
| Live Phoenix collector emit | Optional D3 / `phoenix_live`; **not** DoD if mocks green |
| Global OTEL `register()` side effects | Mitigated by inject factory + `auto_instrument=False` + register only when enabled; prove isolation in unit tests |
| Optional Settings fields | Guide A3: add `phoenix_collector_endpoint` / `phoenix_project_name` with documented defaults — sole attempt gate remains `phoenix_enabled` |
| Envelope double-write + `extras` | Implement must set `phoenix_span_id` before final `write_local_envelope` (guide A5); preserve existing temp→final path + LangSmith extras |
| `build_obs_status` return shape | Today returns `(ObsStatus, langsmith_run_id)`; Implement must thread Phoenix span id without breaking LangSmith callers/tests |

## Locks confirmed (do not reopen)

| Lock | Value |
|------|--------|
| Package / emit | **A** — `arize-phoenix-otel` + `phoenix.otel.register` + one manual chain span |
| Config gate | **A** — `PHOENIX_ENABLED=true` alone (optional endpoint/project overrides) |
| Extras id | **A** — `extras.phoenix_span_id` on success |
| Smoke | Fixture / Kafka-down; never requires Phoenix collector |
| Interview-prep VISION boxes | Human-only — no invent ticks |
| Out | Auto-instrument sprawl, agent-on-consume, Optuna, brokerage, Lowd, full `arize-phoenix` UI dep, fabricated UI shots |

## Implement readiness (numeric)

| Track | Score | READY? | Why not 10 |
|-------|-------|--------|------------|
| **Guide 08 — Phoenix fail-open spans** | **9.0 / 10** | **Yes — READY** | (1) Exact `phoenix.otel.register` / OpenInference attribute / `force_flush` call shape not verified against a pinned installed package version in-repo yet — Soft Adjust at Implement; (2) live collector emit unproven until an operator runs Phoenix on `:6006` (mocks = DoD); (3) global TracerProvider pollution is mitigated on paper but only proven after injectability tests land |

**Overall call:** **READY** for Implement pending hub/human authorize (handoff notes standing authorize if Ready ≥8 — still wait for Implement stage handoff; **this stage does not Implement**).

## Remaining human / hub gate

Hub/Implement authorize per Workflow OS (or standing authorize if Ready ≥8 as handoff states). Spoke must still receive an **Implement** stage / handoff before coding.

Do **not** start coding in this Ready-check stage. Do **not** reopen locks A/A/A.

## Stop

Ready-check complete. **No Implement in this stage.**

## QUALITY self-check (§5)

- [x] Explicit READY + reasons  
- [x] Numeric 0–10 + why not 10  
- [x] Non-blocking residuals listed  
- [x] No implementation started  
- [x] Context ↔ guide ↔ code evidence checked (stub still present; Guide 07 mirror intact)  
- [x] Locks A/A/A confirmed unchanged  
