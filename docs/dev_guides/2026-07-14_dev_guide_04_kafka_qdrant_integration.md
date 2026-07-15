# Dev Guide 04 — Kafka + Qdrant thin integration

**Date:** 2026-07-14  
**Repo:** `alphaguard`  
**Work item:** Guide 04 — Kafka + Qdrant thin integration (§17 delivery + stable point ids + thin `/trigger`)  
**Stage that authored this:** Write-dev-guide (pass 43); Refine-dev-guide (pass 44)  
**Status:** **Implemented** (Guide 04 Implement 2026-07-14)

**Context SSOT:** `alphaguard/docs/2026-07-14_guide04_kafka_qdrant_integration_context_summary.md`  
**Prerequisite:** Guides 01–03 shippable (replay slice, packaging, ≥21 goldens). This guide is the **DE delivery slice** — not Option B, not U4, not live RSS reliability.

---

## Objective

Prove a real **Kafka → validate → embed → idempotent Qdrant upsert** path with ARCHITECTURE §17 semantics, while keeping **fixture smoke Kafka-down**:

1. Compose operator path (Kafka + Qdrant) for `kafka_integration`.  
2. Wire **`kafka_integration`** into `Settings.resource_mode` + `/health` Kafka probe (today hardcoded `skipped`).  
3. Producer + consumer for topic **`news.raw`** (DLQ **`news.raw.dlq`**).  
4. Stable Qdrant point ids (**UUID5**, replace `hash()`).  
5. Thin **`/trigger`** producing into `news.raw`.  
6. Same-delivery VISION / ARCHITECTURE / README / INTERVIEW honesty.

**Success signal:** Reviewer can `docker compose up`, run producer/consumer (or `/trigger`), see idempotent upsert + poison→DLQ tests green, and still `make smoke` / fixture replay **without** Kafka.

---

## Learning notes (new for this guide)

1. **Durable handle vs full agent run** — `PipelineService.run` today does retrieve → Agent 1 → gate (needs Ollama). Kafka **durable handle** for §17 is **validate + Qdrant upsert** (idempotent). Expose that as a method on `PipelineService` (e.g. `ingest_event`) so the consumer does **not** invent a second orchestrator. Full `run()` stays for `/replay` demos.

2. **At-least-once + idempotent upsert** — Kafka may redeliver. Commit offset **only after** upsert succeeds. Same `event_id` → same UUID5 point id → upsert is safe to retry.

3. **Resource mode honesty** — Naming `kafka_integration` in docs while `/health` always skips Kafka is theater. This guide wires the mode and the probe.

4. **Compose ≠ maturity** — Images in `docker-compose.yml` are not a delivery contract until producer/consumer + tests exist.

---

## References (paths only)

- `alphaguard/docs/2026-07-14_guide04_kafka_qdrant_integration_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§5, §15–§17, §16 resource modes)
- `alphaguard/docs/VISION.md`
- `alphaguard/docker-compose.yml`
- `alphaguard/src/alphaguard/contracts/events.py`
- `alphaguard/src/alphaguard/contracts/envelope.py`
- `alphaguard/src/alphaguard/config.py`
- `alphaguard/src/alphaguard/rag/service.py`
- `alphaguard/src/alphaguard/api/app.py`
- `alphaguard/src/alphaguard/pipeline/service.py`
- `alphaguard/src/alphaguard/ingest/replay.py`
- `alphaguard/data/fixtures/replay_events.jsonl`
- `alphaguard/INTERVIEW.md` (§7–§8, §13)
- `second_brain/docs/2026-07-14_prioritize_next_work_guide04_pass40_fan_in.md`
- `second_brain/docs/2026-07-14_refine_context_guide04_pass42_fan_in.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **DE thin integration only.** No Option B / U4 / FinBERT train; no live RSS reliability DoD; no real LangSmith/Phoenix spans; no eval golden growth as primary DoD; no neural reranker.  
2. **`PipelineService` is the sole orchestrator façade.** Consumer calls `PipelineService.ingest_event` (or equivalent) — do **not** create `KafkaOrchestrator`.  
3. **Smoke stays Kafka-down** (`ALPHAGUARD_MODE=replay`, `ALPHAGUARD_RAG_MODE=fixture` → `replay_fixture`).  
4. **Topic / DLQ / group / retries / point id / payload** — soft pins below; do not reopen without human.  
5. **Docs trustworthiness in same delivery** — VISION/ARCHITECTURE/README/INTERVIEW must match shipped Kafka slice without claiming v1 Done.  
6. Prefer ≤300 lines/file (hard max 400) for new ingest modules.

---

## Soft pins (locked defaults — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Topic | `news.raw` |
| DLQ | `news.raw.dlq` |
| Failed durable-handle attempts before DLQ | **3** (`MAX_ATTEMPTS`; DLQ on 3rd failed handle; `run_once` seeks + breaks so commits cannot skip) |
| Consumer group | `alphaguard-news-raw` |
| Point id | `uuid.uuid5(uuid.NAMESPACE_URL, f"alphaguard:event:{event_id}")` — **not** Python `hash()` |
| Kafka client | **`kafka-python`** (sync; no librdkafka). Document if Implement substitutes `confluent-kafka` with green tests |
| Bootstrap | `Settings.kafka_bootstrap_servers` (default `localhost:9092`) |
| `kafka_integration` derivation | `ALPHAGUARD_MODE=live` **and** `ALPHAGUARD_RAG_MODE=qdrant` → `resource_mode=kafka_integration` |
| Durable handle | `NewsEvent` validate + `rag.upsert_event` via `PipelineService.ingest_event` |
| `/trigger` | POST body: NewsEvent fields (± `payload_version`); produce to `news.raw` with key=`event_id` |
| `/trigger` response | JSON `{ "ok": true, "topic": "news.raw", "event_id": "...", "partition": <int|null>, "offset": <int|null> }` (fail-closed 503/502 if Kafka down) |
| Smoke | Unchanged Kafka-down path |
| Module homes | `src/alphaguard/ingest/codec.py`, `producer.py`, `consumer.py` (+ thin CLI wiring in `cli.py` or `ingest/__main__`) |
| Health Kafka probe | When `kafka_integration`: `kafka.KafkaConsumer(bootstrap_servers=..., consumer_timeout_ms=2000)` bootstrap / `topics()` (or AdminClient equivalent) with **2s** timeout — `ok` if connected, else `error`. Never hang smoke. |
| Poison commit policy | After **successful** DLQ produce of the poison payload (or poison envelope), **commit** the original `news.raw` offset so the consumer does not tight-loop. If DLQ produce fails, **do not** commit (retry). |
| Pytest mark | Register marker `kafka_integration`. Default `uv run pytest -q` uses `addopts = "-m 'not kafka_integration'"` (or docs-equivalent). Live Compose tests only when `-m kafka_integration` **or** `ALPHAGUARD_RUN_KAFKA_TESTS=1`. |

### Concrete poison examples (codec / DLQ tests — freeze)

| Case id (test) | Wire defect |
|----------------|-------------|
| `poison_bad_payload_version` | `payload_version: "2"` (unknown) |
| `poison_oou_ticker` | `ticker: "TSLA"` (out of universe) |
| `poison_missing_headline` | omit `headline` |

Happy-path produce may reuse fixture `evt-aapl-001` fields + `payload_version: "1"`.

### Wire payload (flat JSON)

| Field | Required | Notes |
|-------|----------|-------|
| `payload_version` | yes | const `"1"` |
| `event_id` | yes | = Kafka key |
| `headline` | yes | |
| `ticker` | yes | universe-validated |
| `source` | yes | `fixture`\|`rss`\|`kaggle`\|`csv` |
| `published_at` | yes | timezone-aware UTC |
| `url` | no | |

---

## Acceptance criteria (Implement must meet)

- [x] Compose operator path documented; Kafka + Qdrant healthy for `kafka_integration`  
- [x] `resource_mode` can be `kafka_integration`; `/health` probes Kafka when in that mode (not always `skipped`)  
- [x] Producer + consumer for `news.raw`; DLQ `news.raw.dlq` after 3 failed durable handles  
- [x] Offset commit **only after** successful `ingest_event`  
- [x] UUID5 point ids; hash() removed from upsert path  
- [x] Thin `/trigger` produces to `news.raw`  
- [x] Tests: happy path + redelivery idempotency + poison→DLQ; fixture smoke Kafka-down green  
- [x] VISION/ARCHITECTURE/README/INTERVIEW honesty updated same delivery  
- [x] No Option B / U4 / live RSS reliability / real LS spans claimed  

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — Settings + health + UUID5 point ids

- [x] **A1.** Extend `Settings.resource_mode` to return `kafka_integration` when `alphaguard_mode=="live"` and `alphaguard_rag_mode=="qdrant"`; keep `replay_fixture` / `replay_qdrant` otherwise. Update envelope Literal usage if needed.  
- [x] **A2.** `/health`: implement **pinned** Kafka probe (Soft pins). When `kafka_integration`, status `ok`/`error` — **not** unconditional `skipped`. When `replay_*`, Kafka may remain `skipped` with honest detail.  
- [x] **A3.** Replace `abs(hash(event.event_id)) % (2**63-1)` with UUID5 pin in `rag/service.py` upsert. Document local Qdrant rebuild if old hash ids linger.  
- [x] **A4.** Add `PipelineService.ingest_event(event: NewsEvent) -> None` that validates and calls `self.rag.upsert_event(event)`. No second orchestrator class.

### Phase B — Wire codec + producer + consumer

- [x] **B1.** Add dependency `kafka-python` to `pyproject.toml`; `uv sync`.  
- [x] **B2.** `ingest/codec.py`: serialize/deserialize flat payload with `payload_version="1"`; reject the three frozen poison examples.  
- [x] **B3.** `ingest/producer.py`: produce to `news.raw`, key=`event_id`, value=JSON bytes.  
- [x] **B4.** `ingest/consumer.py`: group `alphaguard-news-raw`; parse → `ingest_event`; on success commit; on failure **3 failed durable-handle attempts** then DLQ + **poison commit policy**; **`run_once` seeks failed offset and breaks** (no commit-past-failure). **No silent drop.**  
- [x] **B5.** CLI or `uv run` entrypoints to start consumer + optional one-shot produce from fixture `evt-aapl-001`.

### Phase C — `/trigger` + Compose docs

- [x] **C1.** Add `POST /trigger` thin wrapper; response shape per Soft pins (not a second pipeline).  
- [x] **C2.** Document Compose: `docker compose up -d`, wait for healthchecks, set `ALPHAGUARD_MODE=live` + `ALPHAGUARD_RAG_MODE=qdrant`, start consumer, call `/trigger` or producer.  
- [x] **C3.** Explicit: default smoke / GETTING_STARTED still Kafka-down.

### Phase D — Tests

- [x] **D0.** Register pytest marker `kafka_integration` + default exclude in `pyproject.toml` (`addopts` Soft pin).  
- [x] **D1.** Unit (always on): UUID5 stable for same `event_id`; different ids → different points.  
- [x] **D2.** Unit (always on): codec rejects all three frozen poison examples.  
- [x] **D3.** Marked `@pytest.mark.kafka_integration`: happy upsert via produce→consume (or consumer helper); redelivery idempotent; poison→DLQ after retries + offset committed per policy. Skip unless Compose up / env flag.  
- [x] **D4.** Confirm default `uv run pytest -q` green **without** Kafka.  
- [x] **D5.** Confirm fixture smoke / `make smoke` still does not require Kafka.

### Phase E — Docs honesty + stop

- [x] **E1.** Update VISION status: Live RSS→Kafka E2E / delivery path language — thin integration **proven** for upsert+§17; still not live RSS reliability / not v1 complete.  
- [x] **E2.** Update ARCHITECTURE §15–§17 / module table: producer/consumer/`/trigger` present; hash id residual closed.  
- [x] **E3.** README + INTERVIEW (§7/§8/§13): Compose ≠ maturity fixed; this guide closes thin delivery; smoke still Kafka-down.  
- [x] **E4.** Grep for “Kafka not started” / “hash point id” stale claims; fix.  
- [x] **E5.** Stop. Do not start Option B, U4, live RSS scraper reliability, or real LS/Phoenix.

---

## Verification / Definition of Done

**Done when all are true:**

1. `resource_mode=kafka_integration` reachable; `/health` Kafka probe honest in that mode.  
2. Producer/consumer + DLQ path exist; commit-after-upsert holds.  
3. UUID5 point ids; no `hash()` point id.  
4. `/trigger` produces to `news.raw`.  
5. Targeted tests cover happy / idempotent redelivery / poison→DLQ; non-Kafka suite + smoke green.  
6. VISION/ARCHITECTURE/README/INTERVIEW updated same delivery; no v1-complete / Option B claims.

**Explicitly not required:**

- Live RSS feed reliability / scheduling  
- U4 / Option B train  
- Real LangSmith/Phoenix SDK spans  
- Eval golden growth  
- Claiming portfolio v1 Done  

**Suggested verification commands:**

```bash
# From alphaguard/
docker compose up -d
# wait for kafka + qdrant healthy
rg -n 'uuid5|hash\\(event' src/alphaguard/rag/service.py
rg -n 'kafka_integration|/trigger|news\\.raw' src/alphaguard docs README.md INTERVIEW.md
uv run pytest -q -m 'not kafka_integration'   # or equivalent skip pattern
# With Compose up + MODE=live RAG=qdrant:
#   start consumer; POST /trigger; verify Qdrant point; poison case → DLQ
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke   # still green Kafka-down
```

---

## Blast radius and risks

| Risk | Blast radius | Mitigation |
|------|----------------|------------|
| Second orchestrator | Architecture break | `PipelineService.ingest_event` only |
| Smoke requires Kafka | Stranger/CI fail | Keep replay_fixture; gate integration tests |
| Point-id migration | Stale Qdrant hits | Document rebuild; UUID5 deterministic |
| Full `run()` on every Kafka msg | Ollama load / flake | Durable handle = upsert only |
| Silent poison drop | Data loss theater | DLQ required |
| Option B creep | Calendar burn | Stop conditions |
| Docs claim Compose was always maturity | Interview lie | Phase E honesty |

### Rollback

`git revert` Guide 04 commits; restore hash ids only if needed; `docker compose down`; smoke must still work Kafka-down. Do not leave VISION claiming Kafka proven if code reverted.

---

## Edge-case handling

| Edge case | Expected behavior |
|-----------|-------------------|
| Redelivery same `event_id` | Idempotent upsert; single logical point |
| Invalid ticker / payload_version | Retries then DLQ |
| Kafka down in `kafka_integration` | `/health` error/degraded |
| Kafka down in `replay_fixture` | `/health` Kafka skipped; smoke OK |
| Qdrant down during ingest | Fail durable handle; do not commit; retry/DLQ policy |
| `/trigger` without Kafka | Fail closed with clear error |
| Old hash-id collection | Operator rebuild note |

---

## Stop conditions / non-goals

**Stop when** DoD met. **Do not:** Option B, U4, live RSS reliability, real LS/Phoenix, eval growth as primary, claim v1 Done.

---

## Honest readiness (after Refine pass 44)

- Material invent closed for health probe, module homes, poison examples, pytest gating, poison commit policy, `/trigger` response.  
- Next: **Ready check before code** (not more Refine unless human finds a new gap).  
- Implement only after Ready + human approve.  
