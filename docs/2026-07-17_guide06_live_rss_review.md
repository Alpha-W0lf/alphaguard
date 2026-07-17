# Review — AlphaGuard Guide 06 live RSS (pass 112)

**Date:** 2026-07-17  
**Mode:** spoke  
**Stage:** Review implementation  
**Guide:** `docs/dev_guides/2026-07-17_dev_guide_06_live_rss_reliability.md`  
**Implement:** `d077cb8`  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide06_review_pass112_handoff.md`

## Scope checked

Guide DoD vs `d077cb8` (+ Review must-fix): Yahoo RSS fetch/normalize/produce, CLI one-shot + `--loop`, N=10, agent-on-consume out, fixture smoke default, offline XML tests, docs honesty, MV walkthrough boxes untouched.

## Findings

| Severity | Finding | Tied to | Action |
|----------|---------|---------|--------|
| **Must-fix** | `--max-items` with negative/`0` used Python slice semantics (`events[:-1]` truncates) instead of usage error | Guide soft pin max_items; edge-case / fail-closed CLI | **Fixed** — reject `max_items < 1` in `poll_once` + CLI exit 2; reject `interval_sec < 1` with `--loop` |
| Soft | Live Compose+Yahoo E3 demo not run | Guide E3 residual | Park — not DoD blocker |
| Soft | Context summary still narrates WALKTHROUGH as “RSS later” (historical Gather prose) | Doc drift | **Closed Align pass 116** — context superseded |
| Soft | Mid-ticker Kafka fail after partial produces leaves some messages on topic | At-least-once + idempotent upsert | Acceptable; documented by existing Kafka story |

## Architecture / quality

- No second orchestrator; consumer still `ingest_event` only.
- Smoke defaults unchanged (`Makefile` / `.env.example` / `replay_fixture`).
- File sizes under 300 lines for new `rss_*` modules.
- Tests cover normalize, retries (mocked), poll partial failure, OOU, codec round-trip; `rss_live` excluded by default.

## Verification (Review)

```text
uv run pytest tests/test_rss_*.py -q  → green (incl. new max_items guard)
```

## Shippable call

**Shippable after must-fix** (included in Review commit `2c8f0ea`).  
Fixture smoke remains default. **Align-docs pass 116** refreshed Gather context + status stamps.

## QUALITY §5

- [x] Findings tied to guide  
- [x] Smallest fix set only  
- [x] Honest shippable call  
- [x] No unrelated refactors / no Align  
