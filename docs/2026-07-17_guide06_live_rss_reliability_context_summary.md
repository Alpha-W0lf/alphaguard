# Context: Guide 06 — Live RSS reliability / operator hardening

> **Supersede (Align pass 116):** Guide 06 is **shipped** (Implement `d077cb8` + Review must-fix `2c8f0ea`). Thin Yahoo RSS operator path exists. Do not treat historical Gather “Gap / Not started / RSS later” prose as current truth.

**Date:** 2026-07-17  
**Repos:** `alphaguard`  
**Status:** **Aligned / slice closed** (pass 116) — Review shippable; docs match shipped RSS poll  
**Mode last used:** spoke (pass 116 Align-docs)  
**Stage:** Align-docs complete  
**Dev guide:** `docs/dev_guides/2026-07-17_dev_guide_06_live_rss_reliability.md`  
**Ready-check:** `docs/2026-07-17_guide06_ready_check_before_implement.md`  
**Review:** `docs/2026-07-17_guide06_live_rss_review.md`  
**Role lens:** Data engineer (primary) + backend operator path; interview honesty on reliability claims  

## Outcome (shipped — Align truth)

| Item | Reality |
|------|---------|
| Modules | `ingest/rss_normalize.py`, `rss_fetch.py`, `rss_poll.py` |
| CLI | `alphaguard rss poll [--ticker] [--max-items] [--loop]` |
| Fixture XML | `data/fixtures/rss/yahoo_aapl_sample.xml` |
| Tests | Offline unit tests; `rss_live` + `kafka_integration` excluded by default |
| Smoke | Still Kafka-down **fixture** (`replay_fixture`) |
| Docs | VISION/ARCHITECTURE/README/GETTING_STARTED/INTERVIEW/AGENTS/WALKTHROUGH honest thin-operator language |
| MV walkthrough / daily-prep | **Still unchecked** — human-only |
| Residuals | E3 live Compose+Yahoo demo optional/not required; agent-on-consume still out |

## Problem (historical Gather)

Guides **01–05b** shipped the interview lab. Guide 04 deferred live RSS reliability. Guide 06 closed the honesty gap with a thin Yahoo RSS → Kafka produce operator path (not 24/7 SRE).

**Honest MV note (binding):** VISION Minimum Viable checkboxes for the **10-minute unprompted walkthrough** and **daily hand-coding prep** remain **human-only**. Align does **not** tick those boxes. Outline: `docs/WALKTHROUGH_10MIN.md`.

## Acceptance criteria

- [x] RSS → normalize → `NewsEvent` (`source="rss"`) → existing `produce_event` → `news.raw`
- [x] Stable, idempotent `event_id` for RSS items
- [x] Operator path: Compose + consumer + `rss poll` (one-shot + optional `--loop`)
- [x] Failure modes without silent drop (documented + tested offline)
- [x] Offline unit tests with committed RSS XML fixtures
- [x] Optional `rss_live` gated; default CI never requires Yahoo
- [x] Fixture smoke stays Kafka-down default
- [x] Same-delivery / Align honesty; MV walkthrough still human
- [x] No Agent-on-consume

## Soft pins (LOCKED pass 104 + Review)

| Pin | Locked default |
|-----|----------------|
| Feed | Yahoo Finance RSS per ticker |
| CLI | One-shot DoD + optional `--loop` (interval ≥ 1) |
| Max items | **N=10**; reject `max_items < 1` |
| Watermark | None |
| Smoke | Unchanged `replay_fixture` |
| Agent-on-consume | **Out** |
| Optuna / W&B | **Out** |

## Prior art (current paths)

- `docs/VISION.md` — Guide 06 thin operator path landed; MV walkthrough unchecked  
- `docs/ARCHITECTURE.md` — §6.2 RSS poll present; agent-on-consume deferred  
- `docs/WALKTHROUGH_10MIN.md` — thin `rss poll` (Yahoo may flake)  
- `AGENTS.md`, `README.md`, `GETTING_STARTED.md`, `INTERVIEW.md` — Guide 06 + fixture smoke  
- `src/alphaguard/ingest/rss_{normalize,fetch,poll}.py`  
- `data/fixtures/rss/yahoo_aapl_sample.xml`  
- Guide 04 Kafka path still prerequisite  

## Guide 04 + 06 honesty baseline

| Claim | Reality |
|-------|---------|
| Kafka produce / consume / DLQ / seek-on-failure | **Done** (Guide 04) |
| Idempotent Qdrant upsert (UUID5) | **Done** |
| Default smoke Kafka-down fixture | **Still true** |
| Live RSS thin operator path | **Done** (Guide 06) — not 24/7 reliability |
| Full agent path on consume | **Still out** |

## Open decisions — LOCKED pass 104

Yahoo RSS; one-shot + optional `--loop`; N=10; agent-on-consume out. Do not reopen without human.

## Honest readiness

- **Write / Ready-check / Implement / Review:** **Done** (`d077cb8` + Review `2c8f0ea`).  
- **Align-docs (pass 116):** **Done** — status docs match shipped Guide 06.  
- **Slice:** Guide 06 **closed**.  
- **Will not move** VISION MV walkthrough / daily-prep checkboxes (human rehearsal).

## Learning notes (portable — interview)

- **At-least-once delivery** + **idempotent sink** (UUID5 upsert) is the practical Kafka pattern when exactly-once transactions are out of scope.
- **Bounded retries with exponential backoff and jitter** protect flaky third-party feeds without thundering-herd loops.
- **Operator path ≠ production SRE**: a CLI poll with clear failure modes is an honest DE demo; claiming 24/7 reliability without supervision is interview-toxic.

## QUALITY self-check (§5)

- [x] Context status matches shipped reality (Align)  
- [x] MV human boxes left unchecked  
- [x] Fixture smoke default affirmed  
- [x] Stale Gather “Gap / Not started / RSS later” superseded  
