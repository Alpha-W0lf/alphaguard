# Context: Guide 03 — eval harness ≥20 goldens

**Date:** 2026-07-14  
**Repos:** `alphaguard` (+ program notes in `second_brain`; no other product repos in-slice)  
**Status:** Refined  
**Mode last used:** spoke  
**Stage:** Refine context (pass 27)  
**Handoff:** `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass27_handoff.md`  
**Shared:** `second_brain/docs/2026-07-14_refine_context_guide03_pass27_shared_handoff.md`  
**Prior Refine:** pass 26 → this file; pass-27 note: `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass27.md`  
**Prior Gather:** pass 25 → Draft; gather handoff retained for provenance  
**Lens:** Senior AI eng (eval honesty / interview credibility) + light ML honesty (`bundle_kind=fixture` ≠ Option B metrics)

---

## Problem

Guide 01 shipped a runnable replay-first vertical slice. Guide 02 shipped interview packaging (`INTERVIEW.md`, `GETTING_STARTED.md`, README diagram/stack, `docs/assets/`) — **Review pass-24: shippable**. The next ordered backlog item (pass-12 **#2**, locked as AlphaGuard **guide 03**) is **eval harness growth**: grow `eval/golden_cases.jsonl` from a **7-case stub** to **≥20 goldens** covering schema, identity overwrite, as-of/future-hit rejection, gate determinism, and `SELL`/OOU reject — **without** Kafka E2E and **without** Option B / U4.

| Claim | Reality (2026-07-14 pass-27 re-verify) |
|-------|----------------------------------------|
| Golden count | **7** lines / **7** unique `case_id`s (`wc -l` + JSON parse); **0** duplicate ids |
| By theme | `schema`×2, `identity`×1, `asof`×1, `gate`×2, `oou`×1 |
| Stub sparseness | Several cases are **expect-only** (e.g. `asof_drop_future` has only `case_id`/`check`/`expect`) — not executable without Write inventing payloads; **field skeleton now soft-pinned** (pass 27) |
| Executable harness | **Absent** — `src/alphaguard/eval/` is only `__init__.py` docstring (41 B); loader lives in `tests/test_eval_stubs.py`; assert `len >= 5` only |
| Invariants today | Live in **unit tests** (**20** collected; `test_eval_stubs` green) — INTERVIEW §15 already says this |
| ARCHITECTURE honesty | §5 module map: eval = **Stub** (7 cases); §12 target still ≥20; **§13 screenshots line is stale** (“not present yet” while `docs/assets/` exists) |
| README / INTERVIEW | Both still say grow to ≥20 before portfolio claim |
| Guide 02 | Packaging landed; eval growth was **explicitly out of guide-02 DoD** |
| Not this guide | Kafka E2E; Option B train; U4; live-Ollama numeric schema-pass rates |

**One-sentence problem:** Interview invariants are proven in scattered unit tests, but the committed golden set is still a **7-stub count theater** — short of the ≥20 ARCHITECTURE/pass-12 bar, and not wired as an executable case harness.

---

## Acceptance criteria

Work item success for **guide 03 (when later implemented)** — context pins criteria so Write-dev-guide can freeze DoD. This Refine pass does **not** implement them.

- [ ] `eval/golden_cases.jsonl` contains **≥20** distinct `case_id`s (evidence: `wc -l` / JSON parse ≥20)
- [ ] Cases cover at least these themes (ARCHITECTURE §12 + pass-12): **schema**, **identity** overwrite, **as-of** / future-hit rejection, **gate** determinism (BUY reject vs HOLD/PASS approve), **SELL** reject, **OOU** ticker reject
- [ ] Goldens are **not** count-only theater: a thin **data-driven** path executes each case against real public façades (contracts / `filter_hits_as_of` / `stamp_identity` / `apply_policy` or equivalent) — preferred: pytest parametrize from JSONL
- [ ] `tests/test_eval_stubs.py` (or successor) raises the floor from `>= 5` to **`>= 20`** and asserts theme coverage / required checks present
- [ ] Documented **deferred**: live-Ollama numeric LLM schema-pass rate; Agent 1 hold-out on 50 headlines (VISION Future); Option B metrics; fixture-bundle F1 never quoted as model quality
- [ ] No Kafka producer/consumer; no Option B / U4 / `ml/train`; no packaging redo; no Align-docs VISION checkbox edits required in this guide’s core DoD
- [ ] README Limitations + INTERVIEW §15 updated to match new count/honesty (eval grown; still not live-Ollama numeric rates / not Option B)
- [ ] Existing 20 unit tests remain green; smoke path unchanged (Kafka still not required)

**Refine-stage done when:** accuracy/gaps/stale/edges checked against live evidence; soft defaults pinned; honest Write-dev-guide readiness + score — **met by this file + pass-27 note**.

---

## In scope

- Growing `eval/golden_cases.jsonl` **7 → ≥20** with explicit case themes
- Thin **eval harness** so cases execute (loader + check dispatch / parametrized tests) — not a second orchestration stack
- Tightening the presence/coverage assertion (`>= 20` + theme inventory)
- Updating operator/interview honesty lines that still say “stub ≥5 / grow to ≥20”
- Restating bans: no Kafka, no Option B, no live-Ollama rate theater, fixture≠Option B

### Soft-default theme allocation recipe (Write default — total = 20)

Pin **counts**, not `case_id` strings. Write may rename/reorder within a theme; must keep **sum ≥ 20** and not drop below the soft minima column. Extra fillers (if any) stay on these same themes only.

| Theme (`check`) | Soft default count | Soft minimum | Intent (illustrative — not frozen ids) |
|-----------------|-------------------:|-------------:|----------------------------------------|
| `schema` | **5** | 3 | valid BUY; reject SELL; HOLD ok; PASS ok; one bad-field (confidence OOB **or** confidence string **or** empty rationale) |
| `identity` | **3** | 2 | ticker overwrite; `event_id` overwrite; both mismatch stamped from input |
| `asof` | **4** | 3 | future drop; `available_at == published_at` keep; past-only keep; empty-after-filter |
| `gate` | **6** | 4 | BUY high→reject; HOLD→approve; PASS→approve; BUY below threshold→approve; BUY `== score_threshold`→reject; determinism twin (same inputs → same decision) |
| `oou` | **2** | 2 | TSLA (or equivalent OOU) reject; second OOU symbol **or** fixture-load fail-closed |
| **Total** | **20** | — | `SELL` reject lives under `schema` (existing `schema_reject_sell`); do not invent a parallel unsupported-action theme |

**Explicit non-goal of this recipe:** inventing all 20 `case_id`s in Refine. Exact ids belong in Write-dev-guide / Implement.

### Soft-pinned harness contract (Write should freeze, not reopen)

| Decision | Soft default | Why |
|----------|--------------|-----|
| What “harness” means | JSONL ≥20 + **pytest parametrize** executing each `check` | Count-only = theater |
| Loader home | Move/shared `load_golden_cases` into **`src/alphaguard/eval/`** (thin); tests import it | Package today is docstring-only; loader currently test-local |
| Check dispatch | Small `check` → façade map (`schema`→contracts, `identity`→`stamp_identity`, `asof`→`filter_hits_as_of`, `gate`→`apply_policy`, `oou`→`NewsEvent`/fixture fail-closed) | Keeps eval out of `PipelineService` orchestration |
| Required JSONL keys | Every row: `case_id`, `check`, `expect` (+ unique `case_id`) | Fail closed on load |
| Per-check payloads | **Must be rich enough to execute** — see field skeleton below | Anti-theater |
| Threshold comparisons | Use **live** `gate.manifest.score_threshold` (≈0.45 float noise `0.45000000000000007`) — never hardcode `0.45` in asserts | Avoid float theater |
| Gate force path | Prefer `apply_policy(action, force_score, vol)` — no live LLM, no XGBoost load per case if policy-only | CI speed |
| “Schema pass rate” wording | Treat ARCHITECTURE §12 “schema pass rate” as **structural ok/reject counts on goldens**, **not** live-Ollama numeric LLM rates | Wording trap |

### Soft-default JSONL field skeleton (required keys)

**Universal (every row):** `case_id` (unique), `check`, `expect`.

Loader **fail-closed** if any universal key missing or `case_id` duplicates. Per-`check` keys below are the soft-default payload contract Write freezes; existing sparse stubs must be **enriched** in the same Implement PR.

| `check` | Required payload keys (beyond universal) | Optional / notes | Façade |
|---------|------------------------------------------|------------------|--------|
| `schema` | `action`, `confidence` | May include `rationale`, `event_id`, `ticker`, or hit-shaped fields when testing naive `available_at` / empty rationale — Write picks one bad-field pattern per case | `Agent1Proposal` / `NewsEvent` / `RetrievalHit` validation |
| `identity` | `llm_ticker`, `input_ticker`, `llm_event_id`, `input_event_id` | Enrich existing stub: today only tickers — **must add event_id pair** for executable overwrite of both fields | `PipelineService.stamp_identity` |
| `asof` | `published_at` (aware UTC ISO), `hits` (array of hit objects with at least `document_id`, `text`, `ticker`, `available_at`, `source`) | `expect` values like `future_hit_dropped` / `kept` / `empty` — enrich `asof_drop_future` which is expect-only today | `filter_hits_as_of` |
| `gate` | `action`, `force_score` | Optional `volatility_20d` (default low, e.g. `0.1`); boundary cases set `force_score` from **live** manifest (`==` / just-below), never hardcode `0.45` | `DownsideRiskGate.apply_policy` |
| `oou` | `ticker` | Optional `via: "news_event" \| "fixture"` if Write covers fixture fail-closed as second case | `NewsEvent` validator / fixture loader |

**Hit object minimum inside `asof.hits`:** `document_id`, `text`, `ticker`, `available_at` (aware UTC), `source` (`fixture` or `qdrant`). Aligns with `RetrievalHit`.

---

## Out of scope

- Write-dev-guide / Implement (this stage = Refine context only)
- Kafka E2E / `ingest/producer` / `consumer` / `/trigger` / Compose maturity proof
- Option B `training_events.parquet` / `ml/train` / U4 source lock
- Live-Ollama numeric schema-pass % / Agent 1 50-headline hold-out (VISION Future)
- Growing `data/fixtures/replay_events.jsonl` to ≥20 headlines (ARCHITECTURE §11 debt — **related soft debt**, not locked guide-03 DoD unless human expands)
- Full yfinance completed-session feature builder tests (fixture features today; Option B later)
- Arch import-boundary tests (pass-12 overlooked; separate thin follow-on)
- Real LangSmith/Phoenix SDK spans; LICENSE; packaging redo
- Re-opening guide 01/02 as unshippable; Align-docs VISION / ARCHITECTURE status ticks (note lag only — including §13 screenshots)
- Claiming “eval complete / portfolio-ready / v1 Done”
- Inventing the full ≥20 `case_id` inventory in Refine (allocation recipe replaces it)

---

## Prior art (paths only)

### Product / contracts / agent rails

- `alphaguard/docs/VISION.md` — interview lab purpose; Future “50-headline hold-out” ≠ guide-03 goldens; packaging status **lag** (still “Not started” after guide 02 ship)
- `alphaguard/docs/ARCHITECTURE.md` — §5 eval stub (7); §7.4 gate table (`BUY` reject iff `score >= threshold`); §8 as-of; §10 failure modes; §11 fixtures ≥20 (soft adjacent); §12 testing/eval; §13 **stale** “screenshots not present yet”; §15 build sequence (soft conflict: packaging+eval listed after Kafka/Option B)
- `alphaguard/AGENTS.md` — vertical slice; AG1–AG3; guide 02 packaging landed
- `alphaguard/README.md` — Limitations: eval starts small; grow to ≥20; assets linked
- `alphaguard/INTERVIEW.md` — §15 unit tests vs golden stubs (must update after Implement)
- `alphaguard/GETTING_STARTED.md` — clone/smoke path (unchanged by eval unless cross-link)
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md` — F4 allowed ≥5 with debt to ≥20
- `alphaguard/docs/dev_guides/2026-07-13_dev_guide_02_interview_packaging.md` — eval ≥20 explicitly not required

### Eval / fixtures / code under test

- `alphaguard/eval/golden_cases.jsonl` — **7 stubs** (current SSOT count)
- `alphaguard/src/alphaguard/eval/__init__.py` — stub package (docstring only)
- `alphaguard/tests/test_eval_stubs.py` — load + `len >= 5` (1 test; pass-27 green)
- `alphaguard/tests/test_contracts.py` — schema / SELL / OOU / confidence / naive datetime
- `alphaguard/tests/test_gate.py` — identity stamp; HOLD/PASS approve; BUY reject @ ≥threshold; decide determinism; fail-closed load — **no dedicated BUY-below-threshold approve unit test** (golden gap to fill)
- `alphaguard/tests/test_asof.py` — future `available_at` dropped only (equal-boundary not unit-tested; golden candidate)
- `alphaguard/tests/test_fixtures.py` — sidecar leak drop; OOU fixture fail-closed
- `alphaguard/src/alphaguard/ml/gate.py` — `apply_policy` / `decide` (`>=` reject for BUY)
- `alphaguard/src/alphaguard/pipeline/service.py` — `stamp_identity` (overwrites both `event_id` + `ticker`)
- `alphaguard/src/alphaguard/rag/asof.py` — `filter_hits_as_of` (`available_at <= published_at` keep)
- `alphaguard/data/fixtures/replay_events.jsonl` — **7** events (not ≥20 §11)
- `alphaguard/data/fixtures/model_bundle_fixture/manifest.json` — `bundle_kind=fixture`, `vol_veto_enabled=false`, `score_threshold≈0.45`, synthetic F1=1.0 / `n_rows=64`

### Program / prior Workflow OS passes

- `second_brain/docs/2026-07-13_alphaguard_prioritize_next_work_pass12.md` — **§2 = eval ≥20** (guide 03 lock)
- `second_brain/docs/2026-07-14_gather_context_guide03_pass25_shared_handoff.md` — locked work items; bans
- `second_brain/docs/2026-07-14_alphaguard_gather_context_guide03_pass25_handoff.md` — Gather brief
- `second_brain/docs/2026-07-14_refine_context_guide03_pass26_shared_handoff.md` — prior Refine shared rules
- `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass26.md` — pass 26 note (score 8)
- `second_brain/docs/2026-07-14_refine_context_guide03_pass27_shared_handoff.md` — this Refine shared rules
- `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass27_handoff.md` — this spoke brief
- `second_brain/docs/2026-07-14_alphaguard_review_impl_guide02_pass24.md` — packaging shippable; goldens still 7; Align-docs VISION lag
- `alphaguard/docs/2026-07-13_guide02_interview_packaging_context_summary.md` — style richness prior

### Current golden inventory (evidence)

| `case_id` | `check` | `expect` | Payload richness |
|-----------|---------|----------|------------------|
| `schema_valid_buy` | schema | ok | action + confidence |
| `schema_reject_sell` | schema | reject | action + confidence |
| `identity_overwrite` | identity | AAPL | llm_ticker + input_ticker (**no event_id fields**) |
| `asof_drop_future` | asof | future_hit_dropped | **expect-only** |
| `gate_buy_high_risk_reject` | gate | reject | action + force_score=0.95 |
| `gate_hold_approve` | gate | approve | action + force_score=0.95 |
| `oou_ticker_reject` | oou | reject | ticker=TSLA |

**Count = 7.** Gap to DoD = **≥13** new cases (plus harness wiring + payload enrichment of sparse stubs). Allocation recipe above maps the fill plan without inventing ids.

---

## Risks and blast radius

| Risk | Why it matters | Blast radius | Mitigation for guide 03 |
|------|----------------|--------------|-------------------------|
| **Count theater** | +13 JSONL lines with no executor = fake “eval suite” | Interview kill; contradicts pass-12 anti-theater | Require data-driven execution of each case |
| **Sparse-stub enrichment** | Existing 7 lines lack enough fields to run (`asof`, weak `identity`) | Write invents shapes mid-guide → drift | **Pass-27 field skeleton** soft-pins keys; enrich stubs in same PR |
| **Duplicate / drift vs unit tests** | Two sources of truth diverge | Flaky narrative; maintainer pain | Goldens drive thin checks; keep deep edge cases in unit tests **or** migrate carefully — Write pins one pattern |
| **Fixture F1 / gate metrics leakage** | Cases that “assert F1==1.0” look like Option B proof | ML honesty | Ban Option B metric claims; fixture bundle only for load/score plumbing |
| **Live-Ollama scope creep** | Numeric schema-pass % needs LLM + CI variance; §12 “schema pass rate” wording tempts agents | Calendar; flake | Explicitly deferred; interpret as structural golden counts |
| **Vol-veto cases vs fixture manifest** | Default fixture has `vol_veto_enabled=false` | Confusing fails or fake enables in prod fixture | Synthetic tmp manifest in test only; do not flip committed fixture |
| **Growing replay fixtures “while we’re here”** | §11 ≥20 headlines is separate debt | Scope sprawl into data authoring | Out of scope unless human expands |
| **Kafka / Option B reopen** | Pass-12 / shared handoff bans | Hub ordering | Hard stop conditions |
| **VISION packaging lag** | Status still “Not started” while files exist | Agents may “fix packaging” mid-eval | Note Align-docs; do not Align in guide 03 |
| **ARCHITECTURE §13 screenshot lag** | Still says assets “not present yet”; files exist | Agents may redo packaging screenshots | Align-owned; out of guide-03 DoD |
| **ARCHITECTURE §15 sequence** | Still lists eval after Kafka/Option B | Fresh agents start wrong guide | Cite pass-12 lock: guide 03 = eval |
| **Parametrize explosion** | 20× slow XGBoost loads | CI time | Module-scoped gate fixture; policy-only cases avoid model where possible |
| **Hardcoded 0.45 threshold** | Manifest float is `0.45000000000000007` | Flaky equality / wrong boundary story | Compare via live manifest |
| **INTERVIEW §15 stale after Implement** | Still says stub ≥5 | Interviewer confusion | Update FAQ count/honesty in same guide |
| **False “portfolio-ready” claim** | ≥20 goldens ≠ v1 Done | Status theater | Keep vertical-slice language |
| **Allocation drift** | Write invents uneven theme mix (e.g. 15 schema, 1 asof) | Fake coverage | Soft-default recipe + soft minima; assert theme counts in tests |

---

## Edge cases

| Edge case | Expected guide-03 behavior |
|-----------|----------------------------|
| `available_at == published_at` | Keep hit (≤ filter); case should assert keep, not drop |
| `available_at` slightly after `published_at` | Drop; hard-fail if kept |
| Zero hits after as-of filter | Pipeline still valid path (unit/smoke elsewhere); golden may assert filter emptiness only |
| LLM `event_id` + `ticker` both wrong | Stamp both from input; never score wrong identity |
| `SELL` in proposal | Schema reject — never approve / never silent remap |
| OOU ticker in event / fixture line | Fail closed (`ValidationError` / `FixtureLoadError`) |
| `BUY` score exactly `== score_threshold` | Reject (`>=` policy) — **include boundary golden**; unit test today uses `max(threshold, 0.99)` so exact `==` is weakly covered |
| `BUY` score just below threshold | Approve (absent vol veto) — **no unit test today**; strong golden candidate |
| `HOLD`/`PASS` with extreme score + high vol | Always approve |
| Confidence ignored by policy | Schema validates; gate must not change on confidence alone |
| Malformed golden JSONL line | Loader fails closed in tests (bad case file = CI fail) |
| Duplicate `case_id` | Reject / assert unique ids |
| Missing required `check` / `expect` keys | Fail closed at load |
| Missing per-check skeleton keys | Fail closed (or skip with hard fail) — Write freezes exact behavior |
| Vol veto enabled with missing threshold | GateLoadError (existing unit behavior) — optional golden with tmp manifest |
| CI without Ollama | Goldens must not require live LLM |
| Kafka up/down | Irrelevant to eval DoD |
| Raising assert to ≥20 before JSONL grown | Implement order: cases first or atomic PR — Write sequences steps |
| Naive datetime on `RetrievalHit` | Already unit-tested; good schema/asof golden candidate |
| Empty headline / confidence string | Contract rejects — schema theme fodder |
| Float threshold noise | Never assert `force_score == 0.45`; read manifest |

---

## Unknowns (must resolve or escalate)

| Unknown | Recommended default (pin for Write-dev-guide) | Tradeoff | Blocking? |
|---------|-----------------------------------------------|----------|-----------|
| What “harness” means | **JSONL ≥20 + pytest parametrize executing each `check`** against real façades; keep `src/alphaguard/eval/` thin (loader + optional dispatch helpers) | Pure JSONL growth is cheaper but recreates theater; full eval framework is overkill | **No** — default pinned |
| Loader location | **`src/alphaguard/eval/`** exports loader; tests parametrize | Slightly more package surface than test-only helper | **No** |
| Relationship to existing unit tests | **Keep existing unit tests;** goldens become data-driven coverage of the same themes; do not delete `test_gate` / `test_asof` / `test_contracts` in this guide | Some overlap OK for interview story (“suite + goldens”); dedupe later if noisy | **No** |
| Exact ≥20 case list | **Allocation recipe** (pass 27) replaces full id inventory in Refine; Write drafts ids from recipe | Human may trim/reorder within quotas | **No** |
| JSONL per-check payload schema | **Field skeleton** (pass 27) soft-pins keys; Write freezes names/types in guide | Up-front schema work vs ad-hoc mid-Implement | **No** — skeleton pinned |
| Vol-veto goldens required? | **Optional** (not required for DoD) because committed fixture has veto off; if included, use tmp manifest only | Skipping leaves a policy branch less golden-covered (still code-present) | **No** |
| Grow replay fixtures to ≥20 in same guide? | **Out** (ARCHITECTURE §11 soft debt; separate item) | Misses “fixtures enough for eval demos” aspiration; keeps guide thin | **No** — escalate only if human wants |
| Live-Ollama schema-pass rate | **Deferred** (ARCHITECTURE §12 numeric); structural golden schema checks **in** | Less “LLMOps eval” prestige; honest CI | **No** |
| Import-boundary arch tests | **Out** of guide 03 | Leaves pass-12 overlooked item | Soft |
| Kafka as guide 04 vs after more eval polish | Note only — **not decided here**; pass-12 puts Kafka after packaging; eval is #2; Option B needs U4 | Hub/human | Soft — not blocking Write |
| Align VISION / ARCHITECTURE §13 packaging status mid-guide-03? | **No** — Align-docs separate; context notes lag | Stale VISION/§13 prose remains until Align | **No** |
| Raise `test_golden_cases_present` only vs full runner | Runner **required** (anti-theater) | Slightly more code than count bump | **No** — pinned |

---

## Recommended approach

1. **Write-dev-guide next** for guide 03 only — ordered checklist: freeze per-check JSONL payload shapes (from skeleton) → author ≥20 JSONL cases from **allocation recipe** (enrich sparse stubs) → thin loader/dispatch in `src/alphaguard/eval/` + parametrize → raise assert/`theme` checks → update README Limitations + INTERVIEW §15 → run `uv run pytest` → stop.  
2. **Anti-theater first principle:** a golden without an executor does not count toward DoD.  
3. **Reuse façades already tested:** `Agent1Proposal` / `NewsEvent` validation, `PipelineService.stamp_identity`, `filter_hits_as_of`, `DownsideRiskGate.apply_policy` (force_score style — avoid depending on LLM).  
4. **Do not** touch Kafka, Option B, packaging assets, VISION MV checkboxes, or ARCHITECTURE §13 Align ticks.  
5. **Document deferred** in guide DoD + a short README/INTERVIEW honesty line: numeric live-Ollama rates still out.  
6. **After Implement+Review:** optional Align-docs may refresh VISION packaging lag, ARCHITECTURE §5 “7 cases” → new count, and §13 screenshot “not present yet” → present (Align owns status ticks).

**Triviality check:** Not trivially small — case design + payload enrichment + harness wiring + honesty doc updates + anti-theater discipline. **Do not skip Write-dev-guide.**

---

## Open decisions (human) — defaults pinned; override only if needed

1. **Confirm guide 03 = eval ≥20 goldens** (not Kafka, not Option B) — **default yes** (handoff-locked).  
2. **Harness = executable parametrized goldens** (not JSONL-only) — **default yes**.  
3. **Replay fixture headline growth to ≥20** in this guide? — **default no** (separate debt).  
4. **Vol-veto goldens required?** — **default no** (optional).  
5. **Kafka next as guide 04?** — **open / hub** — note only; does not block Write-dev-guide for eval.  
6. **Align VISION + ARCHITECTURE §13 packaging status before or after guide 03 Implement?** — **default after / separate Align-docs**; do not block eval Write.  
7. **Theme allocation recipe (5/3/4/6/2)** — **default yes**; override only if human wants a different mix with same minima.

---

## Evidence opened this pass (Refine — pass 27)

### Rails / stage / handoffs

- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md` (full)
- `second_brain/docs/workflow_os/rails/ALWAYS.md`
- `second_brain/docs/workflow_os/rails/LEARNING_MODE.md`
- `second_brain/docs/workflow_os/stages/refine-context.md`
- `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass27_handoff.md`
- `second_brain/docs/2026-07-14_refine_context_guide03_pass27_shared_handoff.md`
- `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass26.md`
- Prior Refined context (this file, pass 26)

### Live re-verify (2026-07-14 pass 27)

```bash
# From alphaguard/
wc -l eval/golden_cases.jsonl                 # 7
python3 JSONL parse                           # count=7; unique=7; by_check schema2 identity1 asof1 gate2 oou1
# keys: asof_drop_future = case_id/check/expect only; identity lacks event_id pair
ls src/alphaguard/eval/                       # __init__.py only (41-byte docstring stub)
uv run pytest --collect-only -q               # 20 tests collected
uv run pytest tests/test_eval_stubs.py -q     # 1 passed
wc -l data/fixtures/replay_events.jsonl       # 7
# manifest: bundle_kind=fixture, vol_veto_enabled=false, score_threshold=0.45000000000000007
# docs/assets/: run_envelope_curated.png, smoke_terminal.png present
# Façades read for skeleton: proposals.py, events.py, retrieval.py, gate.apply_policy,
#   pipeline.stamp_identity, rag.asof.filter_hits_as_of
```

**Not run:** full pytest suite / `make smoke` (Refine trusts collect-only + targeted eval stub green; Implement re-verifies).

---

## Learning notes (new this Refine — pass 27)

1. **Allocation recipe vs full inventory** — Quotas per theme close “how many of each?” without pretending Implement authored every `case_id`. That is how Refine lowers Write invent risk without crossing into code.  
2. **Field skeleton as fail-closed design** — Required keys per `check` turn expect-only stubs into an explicit pre-Implement defect. The skeleton is the contract between sparse JSONL and an executable harness.

---

## Honest readiness

- **Write-dev-guide readiness score:** **9.0 / 10** (pass 26 was **8 / 10**; **Δ +1.0**). Ready with carried soft defaults **plus** pass-27 allocation recipe + JSONL field skeleton. **Not 10** because Write still invents concrete `case_id` names + payload *values* — invent risk ≈0 only with a frozen full inventory (explicitly out of this pass).  
- **Ready for Write-dev-guide?** **Yes**  
- **Soft pins closed this pass:** theme allocation recipe (5/3/4/6/2 = 20); JSONL field skeleton (universal + per-check).  
- **Still soft (non-blocking):** exact `case_id` list (Write-owned); optional vol-veto cases; whether hub places Kafka as guide 04; §11 fixture-headline debt; VISION + ARCHITECTURE §13 Align lag.  
- **Still blocking invent risk?** **No hard block** — residual invent is case authorship, not architecture reopen.  
- **Not ready for Implement** until Write (+ optional Refine guide) + Ready-check.  
- **Not ready to claim eval-complete / portfolio-ready** until Implement+Review lands ≥20 **executed** goldens + doc honesty updates.  
- **Status → Refined (pass 27).** Stop for human — no Write-dev-guide / no Implement this pass.

### QUALITY_STANDARD §5 (this Refine)

- [x] Assumptions listed or replaced with evidence / pinned defaults + tradeoffs  
- [x] Did not rush; did **not** invent ≥20 `case_id`s or a runner; did **not** inflate to 10  
- [x] Mode/Stage/artifacts declared (spoke Refine pass 27; this file)  
- [x] Edge cases + blast radius explicit (theater, sparse stubs, veto, boundary, doc lag, float threshold, allocation drift)  
- [x] Findings written to dated context + refine note + handoff Results  
- [x] Spoke stayed in AlphaGuard eval slice; **no Write-dev-guide; no Implement**  
- [x] Verification = paths/commands above; honest Write-dev-guide readiness + score  
