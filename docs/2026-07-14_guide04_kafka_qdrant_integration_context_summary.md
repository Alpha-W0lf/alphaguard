# Context: Guide 04 — Kafka + Qdrant thin integration

**Date:** 2026-07-14  
**Updated:** 2026-07-15 (Align docs — Implemented stamp; pass-49 P1 A1/A3/A4)  
**Repos:** `alphaguard`  
**Status:** **Implemented** (Guide 04 DoD met for default CI path; see residuals)  
**Mode last used:** hub  
**Stage:** Align docs (catch-up after Implement + Review)  
**Role lens:** Data engineer (+ thin backend API)  
**Prioritize SSOT:** `second_brain/docs/2026-07-14_prioritize_next_work_guide04_pass40_fan_in.md`  
**Dev guide:** `docs/dev_guides/2026-07-14_dev_guide_04_kafka_qdrant_integration.md`

## Problem (historical — pre-Implement)

Guides 01–03 shipped replay slice, interview packaging, and ≥21 executable goldens. The remaining major **DE interview gap** was a real Kafka → embed → Qdrant → same `PipelineService` path.

## Outcome (post-Implement 2026-07-14)

| Former gap (pass 42) | Status now |
|----------------------|------------|
| No producer/consumer modules | **Closed** — `ingest/codec.py`, `producer.py`, `consumer.py` |
| `hash()` Qdrant point ids | **Closed** — UUID5 `alphaguard:event:{event_id}` |
| No `/trigger` | **Closed** — `POST /trigger` thin produce to `news.raw` |
| `kafka_integration` not wired | **Closed** — settings + `/health` probe when live+qdrant |

## Acceptance criteria

- [x] Documented Compose operator path: Kafka + Qdrant healthy for `kafka_integration`  
- [x] Wire **`kafka_integration`** into settings/`resource_mode` + `/health` Kafka probe while **smoke stays** `replay_fixture` Kafka-down  
- [x] Topic **`news.raw`**; key = `event_id`; at-least-once; commit offset **only after** durable handling (ARCHITECTURE §17)  
- [x] Wire payload = **versioned NewsEvent JSON** (pinned fields below)  
- [x] Consumer → embed → idempotent Qdrant upsert → **same** `PipelineService` (no second orchestrator)  
- [x] Stable point ids: **UUID5** from `event_id` (replace hash); fixture/replay upsert path consistent  
- [x] Poison path: **3 failed durable-handle attempts** then DLQ topic **`news.raw.dlq`** — no silent-drop  
- [x] Thin **`/trigger`** producing into `news.raw` (in DoD)  
- [x] Same-delivery VISION/ARCHITECTURE/README/INTERVIEW honesty (Compose+delivery for this slice; still not v1 complete)  
- [x] Targeted tests: happy path + redelivery idempotency + poison→DLQ (unit); fixture smoke Kafka-down still green  
- [x] No Option B / U4 / live RSS reliability / real LS spans as DoD  

## Soft pins (locked — wording aligned 2026-07-15)

| Pin | Value |
|-----|--------|
| Topic | `news.raw` |
| DLQ | `news.raw.dlq` |
| Failed durable-handle attempts before DLQ | **3** (`MAX_ATTEMPTS`; DLQ on 3rd failed handle; `run_once` seeks + breaks) |
| Consumer group id | `alphaguard-news-raw` |
| Point id | `uuid.uuid5(uuid.NAMESPACE_URL, f"alphaguard:event:{event_id}")` |
| `/trigger` | Thin produce into `news.raw` |
| Smoke | Remains Kafka-down `replay_fixture` |
| `kafka_integration` | `ALPHAGUARD_MODE=live` + `ALPHAGUARD_RAG_MODE=qdrant` |

### Wire payload (pinned)

Flat JSON object on `news.raw` / DLQ: `payload_version` const `"1"`, `event_id`, `headline`, `ticker`, `source`, `published_at`, optional `url`.

## Residuals (honest — not DoD blockers)

| Residual | Status |
|----------|--------|
| **A2** Live Compose `@pytest.mark.kafka_integration` | **Closed 2026-07-15** — Compose healthy (`bitnamilegacy/kafka:3.9.0` + Qdrant v1.13.2); `ALPHAGUARD_RUN_KAFKA_TESTS=1 pytest -m kafka_integration` → 3 passed (happy / redelivery / poison→DLQ). |
| Option B / U4 / live RSS reliability | Still out of scope |

## In scope (P0 Implement 2026-07-15)

`run_once` seek/commit fix; loop unit tests; §6.2/§17 honesty; VISION status header.

## Out of scope

Option B; U4; live RSS; starting Compose without human ops ask; claiming v1 Done; Kafka transactions.

## Prior art (paths only)

- `docs/ARCHITECTURE.md` (§5, §15–§17, resource modes)  
- `docs/VISION.md` (Live RSS → Kafka E2E = thin integration done)  
- `docker-compose.yml`  
- `src/alphaguard/ingest/{codec,producer,consumer}.py`  
- `src/alphaguard/rag/service.py` (UUID5)  
- `src/alphaguard/api/app.py` (`/trigger`, health)  
- Guide 01–04; Review fan-ins pass 48–49  

## Risks and blast radius

| Risk | Mitigation |
|------|------------|
| Second orchestrator | Binding: `PipelineService` only |
| Smoke requires Kafka | Keep `replay_fixture`; gate integration tests |
| Point-id migration breaks old Qdrant ids | Document collection rebuild for local Qdrant |
| Claiming Compose == maturity | Docs + accepted A2 residual |
| Option B / U4 creep | Hard out |

## Edge cases

- Duplicate `event_id` / redelivery → idempotent upsert (same UUID5 id)  
- Poison → 3 failed attempts then DLQ; commit after successful DLQ produce  
- Kafka/Qdrant down in `kafka_integration` → `/health` degraded/error (not silent skip)  
- Fixture smoke Kafka-down → still green  

## Recommended approach

**Done for Guide 04 code path + P0 seek/commit + A2 Compose proof (2026-07-15).** Next program work via Prioritize (U4 / Option B) — do not reopen Kafka thin path unless changing broker image/policy.
