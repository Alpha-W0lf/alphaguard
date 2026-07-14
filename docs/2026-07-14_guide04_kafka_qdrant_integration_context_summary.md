# Context: Guide 04 — Kafka + Qdrant thin integration

**Date:** 2026-07-14  
**Repos:** `alphaguard`  
**Status:** Refined  
**Mode last used:** hub  
**Stage:** Refine context (pass 41)  
**Prioritize SSOT:** `second_brain/docs/2026-07-14_prioritize_next_work_guide04_pass40_fan_in.md`

## Problem

Guides 01–03 shipped replay slice, interview packaging, and ≥21 executable goldens. The remaining major **DE interview gap** is a real Kafka → embed → Qdrant → same `PipelineService` path. Compose exists (`docker-compose.yml`) but is not maturity; producer/consumer are not started; Qdrant point ids still use `abs(hash(event_id)) % (2**63-1)` in `rag/service.py` (R3 residual). `/trigger` is named in ARCHITECTURE but **not present** yet.

## Acceptance criteria

- [ ] Documented Compose operator path: Kafka + Qdrant healthy for `kafka_integration` mode (`/health` per-dependency honest)  
- [ ] Topic **`news.raw`** (pinned); versioned payload; key = `event_id`; at-least-once; commit offset **only after** durable handling succeeds (ARCHITECTURE §17)  
- [ ] Consumer → embed → idempotent Qdrant upsert → **same** `PipelineService` (no second orchestrator)  
- [ ] Stable point ids: **UUID5** (or equivalent deterministic non-`hash()`) from `event_id` — replace R3 hole; fixture/replay path updated consistently  
- [ ] Poison path: **bounded retries + dead-letter** — soft-pin DLQ topic name **`news.raw.dlq`** (or equivalent documented poison store); do not silent-drop  
- [ ] Resource mode honesty (`kafka_integration`); **fixture smoke stays Kafka-down** (`replay_fixture`)  
- [ ] Thin **`/trigger`** producing into `news.raw` — **in DoD** (ARCHITECTURE already lists it as optional API; today missing — include as thin wrapper)  
- [ ] Same-delivery VISION/ARCHITECTURE/README honesty (Compose proven for this slice; still not v1 complete; §15 soft order override cited)  
- [ ] Targeted tests: happy path + redelivery idempotency + poison→DLQ seam  
- [ ] No Option B / U4 / live RSS / real LS spans as DoD  

## In scope

Kafka + Qdrant thin integration; §17 delivery semantics; stable point ids; thin `/trigger`; docs honesty.

## Out of scope

Option B train; U4; live RSS reliability DoD; real LangSmith/Phoenix spans; neural reranker; claiming v1 Done; expanding eval goldens as primary DoD.

## Soft pins (Refine — do not reopen without human)

| Pin | Value |
|-----|--------|
| Topic | `news.raw` |
| DLQ | `news.raw.dlq` (bounded retries then poison) |
| Point id | Deterministic UUID5 (or documented equivalent) from `event_id` — **not** Python `hash()` |
| `/trigger` | **In DoD** (thin) |
| Smoke | Remains Kafka-down fixture path |

## Prior art (paths only)

- `alphaguard/docs/ARCHITECTURE.md` (§5, §15–§17, resource modes)  
- `alphaguard/docs/VISION.md`  
- `alphaguard/docker-compose.yml`  
- `alphaguard/src/alphaguard/rag/service.py` (hash point id)  
- `alphaguard/src/alphaguard/api/app.py` (`/health`, `/replay`; no `/trigger`)  
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md`  
- Pass 40 fan-in  

## Risks and blast radius

| Risk | Mitigation |
|------|------------|
| Second orchestrator | Binding: `PipelineService` only |
| Smoke requires Kafka | Keep `replay_fixture` smoke; gate integration tests |
| Point-id migration breaks old ids | Document rebuild/reindex for fixture Qdrant; idempotent upsert by `event_id` |
| Option B creep | Hard out |

## Edge cases

- Duplicate `event_id` / redelivery → idempotent upsert  
- Poison message → retries then DLQ  
- Kafka/Qdrant down in `kafka_integration` → `/health` fail-closed honesty  
- Fixture smoke Kafka-down → still green  

## Unknowns (post-Refine)

| Unknown | Status |
|---------|--------|
| Exact JSON payload schema fields for `news.raw` | Soft — Write pins from NewsEvent contract |
| Consumer group id naming | Soft — Write craft |

## Recommended approach

One coherent DE guide: Compose + producer + consumer + §17 + UUID5 point ids + thin `/trigger`.

## Open decisions (human)

- None material for Write — Guide 04 = Kafka/Qdrant confirmed by Prioritize pass 40 unless human overrides to U4/Option B  

## Evidence opened this Refine

- ARCHITECTURE §17 lines 519–528; topic `news.raw` throughout  
- `rag/service.py:68` hash point id  
- API: `/health` present; `/trigger` absent  
- `docker-compose.yml` present  

## Honest readiness

- Ready for Write-dev-guide? **Yes**  
- Soft residuals: exact payload JSON field list (NewsEvent-aligned)  
- Not Implement  
