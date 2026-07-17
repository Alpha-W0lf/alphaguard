# Ready check before code — AlphaGuard Guide 07 (pass 123 / hub 124)

**Status:** Ready-check complete → **READY 9.0/10** — **stop; no Implement in this stage**  
**Guide:** `alphaguard/docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Context:** `alphaguard/docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md`  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide07_ready_check_pass123_handoff.md`  
**Hub:** `second_brain/docs/2026-07-17_hub_fanin_ag_guide07_write_pass124.md`  
**Persistent spoke:** `17e41948-c94b-4547-a428-a3b12eb33e96`

## Declare

Zoom-out Implement readiness. **No coding.** Tom pre-authorized this Ready-check; Implement still needs an explicit authorize (or hub resume). Locks unchanged.

## Checklist

| Question | Verdict |
|----------|---------|
| Context + guide aligned? | **Yes** — Guide 07 = LangSmith real fail-open spans only; Phoenix stub; fixture smoke; MV human-only; matches inventory candidate A + hub locks |
| Current code matches problem statement? | **Yes** — `obs/summary.py` `best_effort_adapters` sets `ok` from key presence with **no SDK emit**; `PipelineService` already maps success+adapter `failed` → `degraded`; `extras` exists on envelope |
| Soft pins unambiguous? | **Yes** — dep `langsmith`; emit when tracing+non-empty key; `Client.create_run`/`update_run` (or equivalent lifecycle); `extras["langsmith_run_id"]`; injectable client; optional `langsmith_live` mark excluded by default |
| Blast radius / rollback clear? | **Yes** — touch `obs/langsmith_adapter.py` (new), `obs/summary.py`, slim `pipeline/service.py`, `pyproject.toml`, docs honesty, tests. Rollback = revert those + drop dep; smoke path unchanged |
| Edge cases planned? | **Yes** — tracing off / empty key → `skipped`; missing package / network / 401 → `failed` fail-open; success+failed → `degraded`; error runs may still attempt emit; never flip approve/reject; no secrets in logs |
| Docs honesty / MV boxes? | **Yes** — Phase C requires same-delivery honesty; walkthrough/daily-prep **not** to be checked; screenshots **out** of DoD |
| Refinements still required before Implement? | **No material** — residuals below are Implement judgment / soft Adjust, not a Refine-dev-guide gate |

## Soft residuals (non-blocking)

| Item | Note |
|------|------|
| Exact `Client.create_run` / `update_run` kwargs | Soft-pin allows equivalent documented lifecycle; pin kwargs at Implement against current `langsmith` docs (Ref lookup unavailable this pass) |
| Live LangSmith emit | Optional D3 / `langsmith_live`; **not** DoD if mocks green |
| Phoenix still key/flag theater | **Locked** — honesty wording only this guide; follow-on guide later |
| Envelope double-write + `extras` | Implement must set `langsmith_run_id` before final `write_local_envelope` (guide A5); preserve existing temp→final path pattern |
| ARCHITECTURE §13 “screenshots not present” | Guide Phase C1 already folds honesty Align for Guide 02 assets |

## Locks confirmed (do not reopen)

| Lock | Value |
|------|--------|
| Scope | LangSmith real fail-open spans only |
| Phoenix | Stub stays |
| Smoke | Fixture / Kafka-down; never requires LangSmith key |
| MV walkthrough / daily-prep | Human-only — no invent ticks |
| Out | Agent-on-consume, Optuna, brokerage, Lowd, fabricated UI shots |

## Implement readiness (numeric)

| Track | Score | READY? | Why not 10 |
|-------|-------|--------|------------|
| **Guide 07 — LangSmith fail-open spans** | **9.0 / 10** | **Yes — READY** | (1) Client create/update kwargs not verified against live LangSmith docs this pass — soft Adjust at Implement; (2) live emit unproven until an operator key exists (mocks = DoD); (3) Phoenix status theater remains by lock (docs honesty only) |

**Overall call:** **READY** for Implement pending hub/human authorize. **This stage does not Implement.**

## Remaining human / hub gate

Say exactly: `Authorize Implement Guide 07` (or hub fan-in → Stage: Implement · Repo: alphaguard · Work item: Guide 07 LangSmith fail-open spans).

Do **not** start coding until that authorize. Do **not** reopen locks.

## Stop

Ready-check complete. **No Implement in this stage.**

## QUALITY self-check (§5)

- [x] Explicit READY + reasons  
- [x] Numeric 0–10 + why not 10  
- [x] Non-blocking residuals listed  
- [x] No implementation started  
- [x] Context ↔ guide ↔ code evidence checked  
- [x] Locks confirmed unchanged  
