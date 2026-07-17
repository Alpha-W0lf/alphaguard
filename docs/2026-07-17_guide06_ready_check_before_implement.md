# Ready check before code — AlphaGuard Guide 06 (pass 106)

**Date:** 2026-07-17  
**Mode:** spoke  
**Stage:** Ready check before code  
**Guide:** `alphaguard/docs/dev_guides/2026-07-17_dev_guide_06_live_rss_reliability.md`  
**Context:** `alphaguard/docs/2026-07-17_guide06_live_rss_reliability_context_summary.md`  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide06_ready_check_pass106_handoff.md`  
**Persistent spoke:** `17e41948-c94b-4547-a428-a3b12eb33e96`

## Declare

Zoom-out Implement readiness. **No coding.** Wait for human approve before Implement. Locks unchanged.

## Checklist

| Question | Verdict |
|----------|---------|
| Context + guide aligned? | **Yes** — Yahoo RSS; one-shot+`--loop`; N=10; agent-on-consume out; fixture smoke; locks marked LOCKED in context |
| Guide 04 prerequisites still present? | **Yes** — `produce_event`, codec, `ingest_event`, `SourceKind` includes `"rss"`, `httpx` in deps, kafka CLI exists |
| Blast radius / rollback clear? | **Yes** — new `ingest/rss_*` + CLI + fixture XML + docs; remove modules/CLI/fixtures and revert honesty lines to roll back; smoke path untouched |
| Edge cases planned? | **Yes** — empty feed, retries, HTML-as-200, malformed item skip, OOU exit 2, Kafka produce fail, partial multi-ticker, Ctrl-C loop |
| Soft pins unambiguous? | **Yes** — URL, UA, timeouts, retries, `event_id`, exit codes, pytest `rss_live` gate |
| Docs honesty / MV boxes? | **Yes** — thin operator path claim only; walkthrough/daily-prep human-only; no invent ticks |
| Refinements still required before Implement? | **No material** — optional micro-note below is Implement judgment, not a Refine gate |

## Soft residual (non-blocking)

| Item | Note |
|------|------|
| All items malformed but XML is a valid channel | Treat like empty → `rss_empty` + exit 0 (same spirit as empty feed) |
| Live Yahoo still flaky | Offline XML = CI truth; live demo residual (guide E3) |
| JSON summary line | “Optional but preferred” — Implement should ship it (cheap; improves operator UX) |
| `rss_poll.py` vs fold into fetch/normalize | File split OK if ≤300 lines; guide already allows either |

## Implement readiness (numeric)

| Track | Score | READY? | Why not 10 |
|-------|-------|--------|------------|
| **Guide 06 — live RSS operator path** | **8.8 / 10** | **Yes — READY** | Live Yahoo not probed this pass; RFC-822 date quirks + stdlib XML edge cases proven only at Implement; tiny “optional JSON summary” preference not a hard pin |

**Overall call:** **READY** for Implement pending human authorization.

## Remaining human gate

Say exactly: `Authorize Implement Guide 06` (or `Stage: Implement` · Repo: alphaguard · Work item: Guide 06 live RSS).

Do **not** start coding until that phrase. Do **not** reopen locks (Yahoo; one-shot+loop; N=10; agent-on-consume out; fixture smoke).

## Stop

Ready-check complete. **No Implement in this stage.**

## QUALITY self-check (§5)

- [x] Explicit READY + reasons  
- [x] Numeric 0–10 + why not 10  
- [x] Non-blocking residuals listed  
- [x] No implementation started  
- [x] Locks confirmed unchanged  
