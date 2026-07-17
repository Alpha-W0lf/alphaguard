# Context: Guide 06 — Live RSS reliability / operator hardening

**Date:** 2026-07-17  
**Repos:** `alphaguard`  
**Status:** Context accepted — Write-dev-guide authored (pass 104); ready for Ready-check / Implement  
**Mode last used:** spoke (pass 104 Write-dev-guide)  
**Stage:** Write-dev-guide complete (Gather was pass 101)  
**Dev guide:** `docs/dev_guides/2026-07-17_dev_guide_06_live_rss_reliability.md`  
**Role lens:** Data engineer (primary) + backend operator path; interview honesty on reliability claims  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide06_gather_pass101_handoff.md`

## Problem

Guides **01–05b** shipped the interview lab: replay-first vertical slice, packaging, ≥21 goldens, Kafka+Qdrant **thin** integration (§17), Option B dataset builder + train CLI. Default smoke remains **fixture** / Kafka-down.

**Gap:** VISION still says live demo = **RSS (Yahoo Finance)**, and ARCHITECTURE §6.2 sketches `RSS → producer → news.raw`. Guide 04 explicitly **deferred** “live RSS feed reliability / scheduling.” Today there is:

- No RSS fetch / parse / normalize module
- No stable `event_id` strategy for live items
- No poll / retry / backoff / empty-feed operator loop
- No fixture RSS XML for offline unit tests
- CLI produce path only loads **fixture** events (`alphaguard kafka produce --event-id …`) or `POST /trigger` with a hand-built body

Interview risk: reviewers who see “Kafka+Qdrant” and “RSS in VISION” may assume a **reliable live ingest story**. Honesty requires either shipping a bounded RSS→Kafka operator path **or** keeping language that RSS is aspirational — Guide 06 closes that honesty gap with a thin, testable reliability slice (not 24/7 production ops).

**Honest MV note (binding):** VISION Minimum Viable checkboxes for the **10-minute unprompted walkthrough** and **daily hand-coding prep** remain **human-only**. This Gather / Guide 06 cannot tick those boxes. Outline exists at `docs/WALKTHROUGH_10MIN.md`; Tom must rehearse aloud.

## Acceptance criteria (proposed for Write-dev-guide)

- [ ] RSS → normalize → `NewsEvent` (`source="rss"`) → existing `produce_event` → `news.raw` (reuse Guide 04 producer/codec; **no second orchestrator**)
- [ ] Stable, idempotent `event_id` for RSS items (same item → same id → same UUID5 Qdrant point)
- [ ] Operator path: documented Compose + consumer + **RSS poll** (one-shot required; optional bounded loop) with timeouts, retries/backoff, and clear exit codes
- [ ] Failure modes handled without silent drop: feed HTTP errors, empty feed, malformed items, out-of-universe ticker skip/log, Kafka produce failure
- [ ] Offline unit tests with **committed RSS XML fixtures** (default CI never requires live Yahoo)
- [ ] Optional live-network probe gated (env / pytest mark) — skip by default; never block smoke
- [ ] Fixture smoke / `make smoke` stays Kafka-down default; no Optuna / W&B / Option B smoke flip
- [ ] Same-delivery honesty: VISION / ARCHITECTURE / README / INTERVIEW / `AGENTS.md` — “thin live RSS operator path” ≠ production reliability ≠ v1 Done; MV walkthrough still human
- [ ] No Agent-on-consume (full `PipelineService.run` on every Kafka message) unless human expands scope

## In scope

- Live RSS **fetch + normalize + produce** into existing Kafka path
- Operator hardening: retries with backoff/jitter, timeouts, User-Agent, per-ticker (or pinned URL template) polling, structured logs
- Dedup via deterministic `event_id` + existing at-least-once consumer + UUID5 upsert
- “Backfill” = **bounded lookback on one poll** (e.g. produce N newest items / items newer than watermark) — not a historical archive rebuild
- Docs + CLI runbook for optional `kafka_integration` demo
- Soft-pin defaults for Write-dev-guide (see Open decisions)

## Out of scope

- **Implement** in this Gather stage
- **Optuna / W&B** / nested HPO changes
- Flipping default smoke to Option B or requiring Kafka for smoke
- Agent-on-consume / wiring Agent 1→2 into the consumer path
- Paid news APIs, scraping HTML news tabs as primary path, multi-provider fan-in
- 24/7 daemon supervisord / systemd / cloud deploy / Kafka transactions / exactly-once
- Lowd Capital, brokerage APIs, neural reranker, real LangSmith/Phoenix SDK spans
- Checking VISION MV walkthrough / daily-prep boxes without Tom’s rehearsal
- Mechanic / Vehicle / AI KB work

## Prior art (paths only)

### Truth / status

- `docs/VISION.md` — Live RSS → Kafka = **thin integration done** (Guide 04); **not** live RSS reliability; MV walkthrough/daily-prep unchecked (human)
- `docs/ARCHITECTURE.md` — §6.2 live path sketch; §10 failure modes; §16 resource modes; §17 Kafka delivery (Guide 04 done)
- `docs/WALKTHROUGH_10MIN.md` — human rehearsal outline; still says live RSS later
- `AGENTS.md`, `README.md`, `GETTING_STARTED.md`, `INTERVIEW.md` — smoke fixture; Guide 04 ≠ RSS reliability

### Guide 04 (prerequisite — done)

- `docs/dev_guides/2026-07-14_dev_guide_04_kafka_qdrant_integration.md` — Implemented; explicitly excludes live RSS reliability
- `docs/2026-07-14_guide04_kafka_qdrant_integration_context_summary.md`
- `src/alphaguard/ingest/{codec,producer,consumer}.py`
- `src/alphaguard/pipeline/service.py` — `ingest_event` durable handle only
- `src/alphaguard/cli.py` — `kafka consume` / `kafka produce` (fixture-only produce today)
- `src/alphaguard/api/app.py` — `POST /trigger`
- `tests/test_kafka_integration.py` (+ codec / point-id unit tests)
- `docker-compose.yml` — `bitnamilegacy/kafka:3.9.0` + Qdrant

### Contracts / config

- `src/alphaguard/contracts/events.py` — `SourceKind` already includes `"rss"`; ticker universe locked
- `src/alphaguard/config.py` — no RSS settings yet (`httpx` already a dependency)
- `src/alphaguard/rag/service.py` — UUID5 `alphaguard:event:{event_id}`

### Product intent (historical)

- `docs/2026-06-21_ai_engineering_in_demand_skills_…brainstorming_conversation.md` — original RSS → Kafka story
- VISION locked: historical = Kaggle/CSV; live demo = Yahoo Finance RSS

## Guide 04 status (honesty baseline)

| Claim | Reality |
|-------|---------|
| Kafka produce / consume / DLQ / seek-on-failure | **Done** |
| Idempotent Qdrant upsert (UUID5) | **Done** |
| `/trigger` + CLI fixture produce | **Done** |
| Compose proof + `kafka_integration` tests | **Done** (opt-in marker) |
| Default smoke Kafka-down fixture | **Still true** |
| Live RSS fetch / schedule / reliability | **Not started** — this Guide 06 |
| Full agent path on consume | **Not started** — ARCHITECTURE §6.2 defers; keep out |

## Risks and blast radius

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| Claim “live RSS reliable” after thin poll CLI | Interview honesty / README trust | Language: **operator demo path** with known Yahoo flakiness; fixture XML = CI truth |
| Yahoo RSS deprecated / 4xx / blocks | Demo fails live | Timeouts + retries; User-Agent; skip-live default; document failure as expected residual |
| Second orchestrator / scrape framework creep | Module bloat, AGENTS file-size | Thin `ingest/rss_*.py`; call existing `produce_event`; ≤300 lines |
| Smoke / CI starts hitting Yahoo | Flaky CI, rate limits | Committed XML fixtures; live mark gated |
| Wrong ticker attribution (headline NLP) | Poison / OOU / wrong RAG context | Prefer **per-ticker feed URL** so ticker is known a priori |
| Unstable `event_id` → duplicate Qdrant points | RAG pollution, non-idempotent demos | UUID5 from stable guid/link+ticker (+ optional published_at) |
| Agent-on-consume sneak-in | RAM (Ollama on every headline), scope weeks | Hard out of Guide 06 |
| Docs drift after Implement | Stale “RSS later” lines | Same-delivery Align of VISION/ARCHITECTURE/README/INTERVIEW/AGENTS |
| MV walkthrough checkbox theater | False portfolio doneness | Explicit: human-only; this guide does not touch those boxes |

## Edge cases

- Empty RSS channel / zero items after filter → exit 0 with structured “nothing to produce” log (not crash)
- HTTP 429 / 5xx / connection timeout → retry with exponential backoff + jitter; then fail closed with non-zero exit for one-shot
- Malformed item (missing title/link/date) → skip item + warn; do not kill whole poll batch unless soft-pin says fail-closed
- Out-of-universe ticker in URL/config → reject before fetch (config validation)
- Duplicate items across polls → same `event_id` → producer may re-send; consumer upsert idempotent (at-least-once OK)
- `published_at` missing / timezone-naive → normalize to UTC or skip with reason
- Feed returns HTML error page as 200 → parse failure → fail closed for that ticker
- Kafka down during RSS poll → produce errors; do not pretend ingest succeeded
- Consumer not running → messages buffer in Kafka (operator must start consumer) — document
- Partial multi-ticker poll (AAPL ok, MSFT fail) → soft-pin: continue others + non-zero if any hard fail (recommend) vs all-or-nothing

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking for Write-dev-guide? |
|---------|----------------|-------------------------------|
| Exact Yahoo URL still serves XML for locked tickers | Soft-pin template + Implement probe; fixture XML for CI regardless | Soft — recommend pin template now; live probe optional |
| Whether Yahoo requires specific User-Agent | Soft-pin browser-like UA in guide | Soft |
| Preferred poll cadence for optional loop | Soft-pin default (e.g. 60–300s) + one-shot as DoD | Soft |
| Watermark persistence (file vs none) | Soft-pin: **none for v1** (bounded N items / poll) unless human wants file watermark | Soft — recommend no watermark file |
| Parser: stdlib `xml.etree` vs `feedparser` | Soft-pin in Write-dev-guide | Soft — recommend stdlib or tiny helper to avoid new dep if possible; `httpx` already present |

## Recommended approach

**Thin RSS producer slice on top of Guide 04 — not a reliability platform.**

1. Add `ingest/rss_fetch.py` (HTTP get with timeout) + `ingest/rss_normalize.py` (XML → `NewsEvent`) + CLI `alphaguard rss poll` (one-shot DoD; optional `--loop`).
2. Soft-pin Yahoo per-ticker headline RSS URL template (VISION-aligned); ticker from URL/config, not NLP.
3. Soft-pin `event_id = uuid5(NAMESPACE_URL, f"alphaguard:rss:{ticker}:{stable_item_key}")` where `stable_item_key` = RSS `guid` else canonical link else hash(title+published_at).
4. Produce via existing `produce_event`; consumer unchanged (`ingest_event` only).
5. Commit 1–2 small RSS XML fixtures under `data/fixtures/rss/`; unit tests parse→NewsEvent→serialize round-trip.
6. Keep smoke fixture; document optional live demo steps in README/GETTING_STARTED.
7. **Next stage:** Ready-check / Implement (hub-gated). Write-dev-guide **done** pass 104.

## Soft pins (LOCKED pass 104 — mirrored in Guide 06)

| Pin | Locked default |
|-----|----------------|
| Feed | Yahoo Finance RSS per ticker: `https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&lang=en-US` |
| HTTP client | Existing `httpx` + timeout 10s + User-Agent header |
| CLI | `alphaguard rss poll` one-shot DoD; optional `--loop --interval-sec` (default 120) |
| Max items / poll | **10** per ticker (bounded backfill); **no** watermark |
| Retries | **3** attempts with exponential backoff + jitter on transport/5xx/429 |
| `event_id` | UUID5 as above from guid/link |
| `source` | `"rss"` |
| Live network tests | Opt-in mark `rss_live` / env; default skip |
| Smoke | Unchanged `replay_fixture` |
| Agent-on-consume | **Out** |
| Optuna / W&B | **Out** |

## Open decisions (human) — LOCKED pass 104

All four Gather decisions are **locked** (see Soft pins + Guide 06). Historical options retained below for audit only — do not reopen without human.

### 1. Feed source and URL template — LOCKED A (Yahoo)

### 2. Operator shape — LOCKED B (one-shot + optional `--loop`)

### 3. Bounded backfill / watermark — LOCKED A (N=10, no watermark)

### 4. Agent-on-consume — LOCKED A (out)

<details><summary>Historical decision text (pre-lock)</summary>

### 1. Feed source and URL template

- **Plain title:** Which live headline source do we soft-pin for Guide 06?
- **In plain terms:** We need a free RSS (or similar) endpoint that yields headlines for our 8 tickers without a paid API key.
- **Options:** (A) Yahoo Finance per-ticker RSS (VISION default) · (B) Different free RSS · (C) Skip live fetch; only `/trigger` + docs (no Guide 06 code)
- **Recommendation:** **A — Yahoo per-ticker RSS**
- **Reasoning:** Matches VISION locked language; ticker known a priori; thin HTTP+XML fits interview DE story; Guide 04 already owns Kafka maturity.
- **Tradeoffs:** Yahoo RSS is historically flaky/deprecated-feeling; demos may fail live — mitigated by fixture XML + honest docs.
- **Needs from you:** Lock A / pick B with URL / park C.

### 2. Operator shape: one-shot vs forever loop

- **Plain title:** What must the operator CLI prove in Definition of Done?
- **In plain terms:** Is a single “fetch and produce now” enough, or must we ship a long-running poll loop?
- **Options:** (A) One-shot only · (B) One-shot + optional `--loop` · (C) Forever daemon as primary
- **Recommendation:** **B**
- **Reasoning:** One-shot is testable and interview-clear; optional loop shows scheduling without pretending we own process supervision.
- **Tradeoffs:** Loop without systemd is still a terminal process; docs must say “demo loop, not production daemon.”
- **Needs from you:** Lock B / prefer A or C.

### 3. Bounded backfill / watermark

- **Plain title:** How do we avoid dumping huge histories or missing “new since last run”?
- **In plain terms:** Each poll can produce the newest N items, or remember a watermark of last seen ids/times.
- **Options:** (A) Newest N only, no watermark · (B) File watermark of last `published_at`/guid · (C) Full feed every time (rely on idempotent upsert only)
- **Recommendation:** **A (N=10)** with idempotent ids; C as acceptable fallback behavior if N omitted carefully
- **Reasoning:** Smallest correct; avoids new state files; UUID5 + Qdrant upsert already absorbs duplicates.
- **Tradeoffs:** Restart after downtime may re-produce recent items (harmless if idempotent) and won’t catch items that fell off the feed window.
- **Needs from you:** Lock A / ask for B.

### 4. Agent-on-consume (confirm out)

- **Plain title:** Should Guide 06 also run Agent 1→2 when Kafka messages arrive?
- **In plain terms:** Today the consumer only upserts to Qdrant. Running the full LLM+gate path on every headline is a different product slice.
- **Options:** (A) Keep out (upsert only) · (B) Add agent-on-consume in same guide
- **Recommendation:** **A — keep out**
- **Reasoning:** Matches ARCHITECTURE §6.2; protects 16GB RAM story; keeps Guide 06 finishable.
- **Tradeoffs:** Live demo still needs separate `/replay` (or later guide) for agent path after RSS fills Qdrant.
- **Needs from you:** Confirm A (default) or expand to B.

</details>

## Evidence opened this pass

- `second_brain/docs/workflow_os/rails/{QUALITY_STANDARD,ALWAYS,LEARNING_MODE}.md`
- `second_brain/docs/workflow_os/stages/gather-context.md`
- `second_brain/docs/2026-07-17_spoke_alphaguard_guide06_gather_pass101_handoff.md`
- `alphaguard/docs/{VISION,ARCHITECTURE,WALKTHROUGH_10MIN}.md`
- `alphaguard/docs/dev_guides/2026-07-14_dev_guide_04_kafka_qdrant_integration.md` (+ Guide 04 context)
- `alphaguard/src/alphaguard/ingest/{producer,consumer,codec}.py`
- `alphaguard/src/alphaguard/{cli,config,pipeline/service,contracts/events}.py`
- `alphaguard/{README,GETTING_STARTED,INTERVIEW,AGENTS}.md` (grep + selective read)
- Web check: Yahoo RSS URL pattern still cited as `feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}` (flaky/deprecated caveats noted)

## Honest readiness

- **Write-dev-guide:** **Done** (pass 104) — `docs/dev_guides/2026-07-17_dev_guide_06_live_rss_reliability.md`.
- **Ready for Ready-check / Implement?** Yes after hub authorizes — locks applied; DoD executable.
- **Will not move** VISION MV walkthrough / daily-prep checkboxes from this work alone (human rehearsal).

## Learning notes (portable — interview)

- **At-least-once delivery** + **idempotent sink** (UUID5 upsert) is the practical Kafka pattern when exactly-once transactions are out of scope.
- **Bounded retries with exponential backoff and jitter** protect flaky third-party feeds without thundering-herd loops.
- **Operator path ≠ production SRE**: a CLI poll with clear failure modes is an honest DE demo; claiming 24/7 reliability without supervision, SLOs, and DLQ ops is interview-toxic.

## QUALITY self-check (§5)

- [x] Assumptions listed; unknowns explicit
- [x] Edge cases + blast radius (≥2 angles: interview honesty, CI flakiness, RAM/scope)
- [x] Findings written to artifact path
- [x] Spoke stayed in Guide 06 Gather slice; no Implement / Optuna
- [x] Open decisions have recommendation + reasoning + tradeoffs (mirrored in chat)
- [x] Honest readiness: Write-dev-guide next; MV walkthrough human
