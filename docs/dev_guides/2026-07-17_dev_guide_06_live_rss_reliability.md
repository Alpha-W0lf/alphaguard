# Dev Guide 06 — Live RSS reliability / operator hardening

**Date:** 2026-07-17  
**Repo:** `alphaguard`  
**Work item:** Guide 06 — Yahoo RSS → normalize → Kafka produce (operator path) on top of Guide 04  
**Stage that authored this:** Write-dev-guide (pass 104)  
**Status:** **Ready for Implement** (no code in this stage)

**Context SSOT:** `alphaguard/docs/2026-07-17_guide06_live_rss_reliability_context_summary.md`  
**Prerequisite:** Guides 01–05b shippable. Guide 04 Kafka thin integration **done** (producer/consumer/`/trigger`/UUID5/DLQ). Default smoke remains fixture / Kafka-down.

**Human locks (pass 104 — do not reopen):**

| Lock | Value |
|------|--------|
| Feed | Yahoo Finance per-ticker RSS |
| CLI | One-shot DoD + optional `--loop` |
| Backfill | Newest **N=10** per ticker; **no** watermark file |
| Agent-on-consume | **Out** (consumer stays `ingest_event` upsert only) |
| Smoke | Fixture / Kafka-down default unchanged |
| Optuna / W&B | **Out** |
| VISION MV walkthrough / daily-prep checkboxes | **Human-only** — do not invent ticks |

---

## Objective

Ship a **thin, honest live RSS operator path**: fetch Yahoo Finance RSS for locked tickers → normalize to `NewsEvent` (`source="rss"`) → produce into existing `news.raw` via Guide 04 `produce_event` — with timeouts, retries/backoff, bounded backfill (N=10), offline XML fixtures, and docs that do **not** claim production reliability or v1 Done.

**Success signal:** Operator can `docker compose up`, start consumer, run `alphaguard rss poll` (one-shot), see items land on `news.raw` → Qdrant upsert; unit tests pass on committed XML **without** hitting Yahoo; `make smoke` still Kafka-down fixture.

---

## Learning notes (new for this guide)

1. **Source adapter vs durable handle** — RSS fetch/normalize is an **ingress adapter**. Kafka durable handle remains Guide 04 (`ingest_event` → upsert). Do not invent `RssOrchestrator` or call `PipelineService.run` from the poller.
2. **Idempotent live ids** — Live items need stable `event_id`s so at-least-once produce + UUID5 Qdrant upsert stay safe across re-polls.
3. **Operator path ≠ SRE** — Optional `--loop` is a demo scheduler in a terminal, not systemd/SLO-backed reliability. Docs must say so.
4. **Fixture XML is CI truth** — Live Yahoo may 4xx/block; never make default pytest depend on the network.

---

## References (paths only)

- `alphaguard/docs/2026-07-17_guide06_live_rss_reliability_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§6.2 live path, §10 failure modes, §16–§17)
- `alphaguard/docs/VISION.md` (RSS live demo language; MV human boxes)
- `alphaguard/docs/WALKTHROUGH_10MIN.md` (do not auto-check)
- `alphaguard/docs/dev_guides/2026-07-14_dev_guide_04_kafka_qdrant_integration.md`
- `alphaguard/src/alphaguard/ingest/{codec,producer,consumer}.py`
- `alphaguard/src/alphaguard/contracts/events.py` (`SourceKind` includes `"rss"`)
- `alphaguard/src/alphaguard/config.py`
- `alphaguard/src/alphaguard/cli.py`
- `alphaguard/src/alphaguard/pipeline/service.py` (`ingest_event` only — do not expand)
- `alphaguard/{README,GETTING_STARTED,INTERVIEW,AGENTS}.md`
- `alphaguard/pyproject.toml` (pytest markers / `httpx` already present)
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **RSS producer slice only.** Reuse Guide 04 producer/codec/consumer. No second orchestrator. No Agent-on-consume. No Optuna/W&B. No Option B smoke flip.
2. **`PipelineService` remains sole run/ingest façade.** Poller may call `produce_event` only; consumer still calls `ingest_event` only.
3. **Smoke stays Kafka-down** (`replay_fixture`). Live RSS never required for `make smoke` or default `uv run pytest -q`.
4. **Ticker from feed config, not NLP.** Per-ticker Yahoo URL; reject OOU before fetch.
5. **Docs trustworthiness in same delivery** — VISION/ARCHITECTURE/README/INTERVIEW/AGENTS/WALKTHROUGH honesty: thin operator path landed; not production reliability; not v1 Done; MV walkthrough still human.
6. Prefer ≤300 lines/file (hard max 400) for new `ingest/rss_*.py` modules.
7. No secrets in git; no paid news APIs; no HTML scrapers as primary path.

---

## Soft pins (locked — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Feed URL template | `https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&lang=en-US` |
| Tickers | Locked universe from `TICKER_UNIVERSE` (`AAPL`…`QQQ`); CLI `--ticker AAPL` or `--ticker all` |
| HTTP | `httpx` GET; timeout **10s**; User-Agent `AlphaGuard/0.1 (+https://github.com/Alpha-W0lf/alphaguard; research)` |
| Retries | **3** attempts on transport / timeout / HTTP 429 / 5xx; exponential backoff + jitter (base ~0.5s, cap ~8s) |
| Fail-closed after retries | One-shot exits **non-zero** if any requested ticker hard-fails fetch/parse-as-feed |
| Partial multi-ticker | Continue other tickers; exit non-zero if **any** hard failure |
| Malformed **item** | Skip item + warn; do not fail whole ticker if ≥1 valid item remains |
| Empty feed / zero valid items | Exit **0** for that ticker with structured log `rss_empty` (not a crash) |
| Max items / poll | **10** newest per ticker (order: feed order as returned; take first 10 valid after parse) |
| Watermark file | **None** |
| `source` | `"rss"` |
| `event_id` | `str(uuid.uuid5(uuid.NAMESPACE_URL, f"alphaguard:rss:{ticker}:{stable_item_key}"))` where `stable_item_key` = RSS `guid` if present else canonical `link` else `sha256(f"{title}|{published_at_iso}")[:32]` |
| `published_at` | Parse RSS date → timezone-aware **UTC**; if missing/unparseable → **skip item** + warn |
| Parser | stdlib `xml.etree.ElementTree` (no new `feedparser` dep unless Implement proves stdlib insufficient — document if substituted) |
| Module homes | `src/alphaguard/ingest/rss_fetch.py`, `rss_normalize.py` (+ thin poll orchestration in one of those or `rss_poll.py` if needed for ≤300 lines); wire CLI in `cli.py` |
| CLI | `alphaguard rss poll [--ticker AAPL\|all] [--max-items 10] [--loop] [--interval-sec 120]` |
| Loop default interval | **120** seconds when `--loop` set |
| Loop semantics | Demo only; KeyboardInterrupt clean exit; sleep between full universe/ticker polls |
| Produce | Existing `create_producer` + `produce_event`; flush/close on exit |
| Consumer | **Unchanged** — no Agent-on-consume |
| Fixture XML | `data/fixtures/rss/yahoo_aapl_sample.xml` (+ optional second ticker); small, redistributable |
| Pytest | Always-on unit tests for normalize + `event_id` stability + skip-malformed; optional `@pytest.mark.rss_live` gated by env `ALPHAGUARD_RUN_RSS_LIVE=1`; default `addopts` excludes `rss_live` **and** keeps excluding `kafka_integration` |
| Smoke | Unchanged fixture path |
| Docs claim | “Thin live RSS operator path” — **not** 24/7 reliability, **not** v1 Done |

### CLI exit codes (freeze)

| Code | Meaning |
|------|---------|
| `0` | Success (including empty-but-healthy feeds with zero produces) |
| `1` | Partial/hard failure after retries (any ticker fetch/parse-as-feed/produce failure) |
| `2` | Usage / config error (OOU ticker, bad args) |

### JSON summary line (optional but preferred)

One-shot prints a final JSON object to stdout (in addition to logs), e.g.:

```json
{
  "ok": true,
  "tickers": ["AAPL"],
  "fetched": 1,
  "produced": 3,
  "skipped_items": 1,
  "errors": []
}
```

---

## Acceptance criteria (Implement must meet)

- [ ] Yahoo RSS fetch + normalize → `NewsEvent` (`source="rss"`) → `produce_event` → `news.raw`
- [ ] Stable `event_id` (same item → same id); UUID5 Qdrant path unchanged
- [ ] CLI `alphaguard rss poll` one-shot DoD; optional `--loop --interval-sec`
- [ ] N=10 max items; no watermark file; retries/backoff/timeouts/User-Agent as pinned
- [ ] Edge cases: empty feed exit 0; malformed item skip; OOU reject before fetch; Kafka produce failure → non-zero; partial multi-ticker continue + non-zero
- [ ] Committed RSS XML fixtures + always-on unit tests (no live Yahoo in default CI)
- [ ] Optional `rss_live` mark skipped by default
- [ ] Consumer **not** changed to call `PipelineService.run`
- [ ] `make smoke` / default pytest still Kafka-down fixture green
- [ ] Same-delivery docs honesty (VISION/ARCHITECTURE/README/GETTING_STARTED/INTERVIEW/AGENTS/WALKTHROUGH); **no** MV walkthrough/daily-prep checkbox invent
- [ ] No Optuna/W&B; no paid APIs; no HTML scrape primary path

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — Normalize + fixtures (offline first)

- [ ] **A1.** Add `data/fixtures/rss/yahoo_aapl_sample.xml` with ≥3 `<item>`s (title, link, guid, pubDate) plus one deliberately malformed item (e.g. missing title) for skip tests.
- [ ] **A2.** `ingest/rss_normalize.py`: parse XML bytes → list of `NewsEvent` for a given `ticker`; apply `event_id` pin; `source="rss"`; UTC `published_at`; skip malformed items with warning.
- [ ] **A3.** Unit tests: happy parse count; malformed skipped; same guid → same `event_id`; different guids → different ids; OOU ticker rejected at API boundary (caller validates ticker ∈ universe before normalize/fetch).
- [ ] **A4.** Round-trip: normalized event → `serialize_event` / `deserialize_bytes` succeeds (`payload_version="1"`).

### Phase B — Fetch + retries

- [ ] **B1.** `ingest/rss_fetch.py`: `fetch_feed(ticker) -> bytes` using URL template + httpx timeout + User-Agent; retries as pinned; raise typed error after exhaustion.
- [ ] **B2.** Unit tests: mock httpx (or injectable transport) for 200 XML, 500 then 200, and hard-fail after 3 attempts — **no live network**.
- [ ] **B3.** Optional: register pytest mark `rss_live`; one skipped-by-default test that hits Yahoo for `AAPL` when `ALPHAGUARD_RUN_RSS_LIVE=1`. Update `pyproject.toml` `addopts` to exclude `rss_live`.

### Phase C — Poll orchestration + CLI

- [ ] **C1.** Poll helper: for each requested ticker → fetch → normalize → take ≤`max_items` → `produce_event` each; aggregate counts/errors per exit-code table.
- [ ] **C2.** Wire `alphaguard rss poll` in `cli.py` with `--ticker`, `--max-items` (default 10), `--loop`, `--interval-sec` (default 120).
- [ ] **C3.** One-shot path is DoD; `--loop` sleeps between iterations until KeyboardInterrupt.
- [ ] **C4.** Do **not** modify `NewsRawConsumer` / `ingest_event` to run Agent 1→2.

### Phase D — Operator docs + honesty

- [ ] **D1.** README + GETTING_STARTED: optional section — Compose up → `kafka consume` → `rss poll --ticker AAPL` → note consumer must be running; smoke still Kafka-down.
- [ ] **D2.** VISION progress row: Live RSS reliability → **thin operator path landed** (not production reliability / not v1 Done). Do **not** check MV walkthrough or daily-prep boxes.
- [ ] **D3.** ARCHITECTURE §6.2 / component table: RSS fetch present; still optional; agent-on-consume still deferred.
- [ ] **D4.** INTERVIEW / AGENTS / WALKTHROUGH: replace “live RSS later” with honest “thin poll CLI; Yahoo may flake; fixture smoke default.”
- [ ] **D5.** Grep stale claims (“RSS reliability done”, “v1 complete”, “live RSS later” contradictions); fix.

### Phase E — Verification + stop

- [ ] **E1.** `uv run pytest -q` green without Kafka/Yahoo.
- [ ] **E2.** `make smoke` still fixture / Kafka-down.
- [ ] **E3.** Manual optional (operator): Compose + consume + `rss poll` once when network allows — record outcome in Implement notes; live failure is residual, not DoD blocker if offline tests green.
- [ ] **E4.** Stop. Do not start Agent-on-consume, Optuna, Option B smoke flip, or walkthrough checkbox edits.

---

## Verification / Definition of Done

**Done when all are true:**

1. Offline unit tests prove normalize + stable ids + fetch retries (mocked) + codec round-trip.  
2. CLI `alphaguard rss poll` one-shot exists; optional `--loop` works without claiming daemon maturity.  
3. Produces into `news.raw` via existing producer; consumer path unchanged (upsert only).  
4. Default pytest + `make smoke` green without Kafka or live Yahoo.  
5. Docs honesty updated same delivery; MV human boxes untouched.  
6. No Agent-on-consume; no Optuna/W&B; N=10; Yahoo URL template as locked.

**Explicitly not required:**

- Yahoo live success in CI  
- 24/7 process supervision / systemd  
- Watermark persistence  
- Agent 1→2 on consume  
- Flipping default smoke off fixture  
- Checking VISION walkthrough / daily-prep boxes  

**Suggested verification commands:**

```bash
# From alphaguard/
uv run pytest -q
make smoke

# Optional operator demo (Compose + network):
docker compose up -d
export ALPHAGUARD_MODE=live ALPHAGUARD_RAG_MODE=qdrant
uv run alphaguard kafka consume   # separate terminal
uv run alphaguard rss poll --ticker AAPL --max-items 10

# Optional live network test:
ALPHAGUARD_RUN_RSS_LIVE=1 uv run pytest -m rss_live -q
```

---

## Blast radius and risks

| Risk | Impact | Mitigation in this guide |
|------|--------|--------------------------|
| Docs overclaim “reliable live ingest” | Interview trust | Explicit “thin operator / Yahoo may flake” language |
| Default CI hits Yahoo | Flaky PRs | Fixture XML + exclude `rss_live` |
| Second orchestrator / scrape framework | Scope + file-size rails | Thin `rss_*` + `produce_event` only |
| Unstable ids → duplicate Qdrant points | RAG pollution | UUID5 `event_id` pin from guid/link |
| Agent-on-consume creep | RAM + weeks of scope | Hard out; Phase C4 / E4 stop |
| Smoke requires Kafka | Breaks clone path | Smoke unchanged `replay_fixture` |
| MV checkbox theater | False portfolio doneness | Human-only; D2 forbids ticks |

---

## Edge-case handling (must appear in Implement or tests)

| Case | Required behavior |
|------|-------------------|
| Empty channel / zero valid items | Log `rss_empty`; exit 0 for healthy empty |
| HTTP 429/5xx/timeout | Retry ×3 with backoff+jitter; then hard-fail ticker |
| HTML body with HTTP 200 | Parse-as-feed failure → hard-fail ticker |
| Missing title/link/date on item | Skip item + warn |
| OOU `--ticker TSLA` | Exit 2 before network |
| Duplicate poll of same guid | Same `event_id`; idempotent downstream upsert |
| Kafka down on produce | Non-zero exit; do not claim success |
| Multi-ticker partial failure | Continue; exit 1 if any hard fail |
| `--loop` + Ctrl-C | Clean shutdown; no traceback spam required beyond KeyboardInterrupt handling |

---

## Out of scope (stop list)

- Implement in this Write stage  
- Agent-on-consume / `PipelineService.run` on Kafka messages  
- Optuna / W&B / HPO changes  
- Watermark files; systemd; cloud Kafka  
- Paid news APIs; HTML news-tab scraping as primary  
- Neural reranker; Lowd Capital; brokerage  
- Inventing VISION MV walkthrough / daily-prep checkmarks  

---

## Honest readiness

- **Write-dev-guide DoD:** met when this file exists with steps, soft pins, DoD, blast radius, edge cases.  
- **Next stage:** Ready-check before code (or Implement if hub authorizes directly).  
- **Not started:** any application code for RSS.

## QUALITY self-check (§5)

- [x] Executable steps + DoD + verification commands  
- [x] Edge cases + blast radius explicit  
- [x] Locks mirrored from handoff (Yahoo; one-shot+loop; N=10; agent-on-consume out; fixture smoke)  
- [x] No implementation in this stage  
- [x] Docs honesty + human MV boxes called out  
