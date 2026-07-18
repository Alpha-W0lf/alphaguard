# Context: Guide 08 — Phoenix real fail-open spans

**Date:** 2026-07-18  
**Repos:** `alphaguard`  
**Status:** **Guide 08 Align Met (pass 152)** — slice closed; docs match shipped reality  
**Mode last used:** spoke (pass 152 Align-docs)  
**Stage:** Align-docs (complete) — Guide 08 closed; hub Prioritize for next work  
**Role lens:** Senior AI eng (LLMOps honesty / fail-open telemetry)  
**Guide path:** `docs/dev_guides/2026-07-18_dev_guide_08_phoenix_fail_open_spans.md`  
**Review:** `docs/2026-07-18_guide08_phoenix_fail_open_review.md` (shippable as-is)  
**Implement:** `e5aad97` · Review docs: `a60a417`  
**Align handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_align_guide08_phoenix_pass152_handoff.md`

## Outcome (Align pass 152 — supersedes Gather “stub” prose)

| Item | Reality after Guide 08 |
|------|------------------------|
| Phoenix | **Real fail-open OTEL chain spans** when `PHOENIX_ENABLED` (`obs/phoenix_adapter.py` / `arize-phoenix-otel`); `ok` only after span+`force_flush`; else `skipped`/`failed`; `extras.phoenix_span_id` on success |
| LangSmith | Unchanged Guide 07 real fail-open Client spans |
| Default smoke | Fixture / Kafka-down; `obs.phoenix=skipped` — **never** requires Phoenix collector |
| Interview-prep VISION boxes | Still **unchecked** (human-only) |
| Soft residuals | D3 live Phoenix probe optional; OTEL flush-True-on-dead-collector quirk — parked, non-blocking |

## Problem (historical Gather — pass 151)

Guide 07 closed LangSmith status theater. Phoenix still had the **same honesty gap**: `PHOENIX_ENABLED` → `obs.phoenix=ok` without SDK emit. That gap is **closed** by Guide 08.

## Acceptance criteria (historical Gather — now Met)

- [x] When Phoenix is configured, adapter emits **at least one real OpenTelemetry / OpenInference span** — not flag-presence theater  
- [x] `obs.phoenix=ok` **only after** successful emit+flush; else `skipped`/`failed`  
- [x] Default smoke / default pytest: `PHOENIX_ENABLED=false` → `skipped`  
- [x] Fail-open relative to gate; may `degraded`  
- [x] Local run summary remains mandatory  
- [x] Unit tests with mocks; optional `phoenix_live` excluded by default  
- [x] Same-delivery docs honesty — **no** invent Interview-prep ticks  
- [x] No secrets in git; no fabricated Phoenix UI screenshots required  

## Locked decisions

**Locked (Tom pass 152 A/A/A):** `arize-phoenix-otel` + one manual chain span; `PHOENIX_ENABLED` alone; `extras.phoenix_span_id`; fixture smoke default; Interview-prep human-only.

## Soft residuals (parked)

- Optional D3 live Phoenix operator probe  
- OTEL `force_flush` may return True when dead-collector export logs failures (mocks still assert False → failed)  

## Honest readiness

- **Guide 08 lifecycle:** Gather → Write → Ready-check (9.0) → Implement → Review (shippable) → **Align Met**.  
- **Slice closed.** Do **not** invent next Guide without hub Prioritize + handoff.  
- **Will not** tick Interview-prep walkthrough / daily-prep from any agent stage.

## QUALITY self-check (§5)

- [x] Outcome supersedes stale Gather “stub” prose  
- [x] Human Interview-prep lanes still explicit / unchecked  
- [x] Soft residuals parked  
- [x] Align-docs only — no Implement / no next-guide invent  

## Gather archive note

Full Gather prior-art / risk / open-decision prose lived in pass 151; Tom locked A/A/A; Implement `e5aad97` shipped the thin adapter. Prefer **Outcome** table above for current truth.
