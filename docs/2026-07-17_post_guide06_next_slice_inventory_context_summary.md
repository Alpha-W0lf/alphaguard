# Context: Post–Guide 06 agent-movable next-slice inventory

**Date:** 2026-07-17  
**Repos:** `alphaguard`  
**Status:** Write-dev-guide authored (pass 123) — Guide 07 locks locked; Ready-check next  
**Mode last used:** spoke (pass 123 Write-dev-guide)  
**Stage:** Write-dev-guide (complete) → Ready-check before code  
**Role lens:** Senior AI eng (LLMOps / interview honesty) + light DE  
**Guide 07 path:** `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Write handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide07_write_pass123_handoff.md`  
**Hub:** `second_brain/docs/2026-07-17_hub_fanin_ag_gather_authorize_write_pass123.md`  
**Prior Gather handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_next_gather_pass121_handoff.md`  
**Guide 06 closed:** Align Met pass 118 (`d795005`); Review shippable `2c8f0ea`

## Problem

Guides **01–06** (incl. 05a/05b) shipped the vertical slice + Option B lab train + thin Yahoo RSS poll. Portfolio doneness is still capped by **human** VISION MV boxes (10-min walkthrough; daily hand-coding) — agents must **not** tick those.

Remaining **agent-movable** gaps are scattered: LLMOps adapters are **status stubs** (no real LangSmith/Phoenix spans), Guide 06 soft residuals (optional live Yahoo demo), and optional U4/training hygiene (FB→META alias soft pin) that is **not** blocking Option B already landed. Without an explicit next guide, the spoke idles while interview story still claims LangSmith maturity it does not prove.

## Human-only lanes (do not propose ticking)

| VISION MV box | Owner | Agent action |
|---------------|-------|--------------|
| 10-min unprompted architecture walkthrough | Tom — rehearse `docs/WALKTHROUGH_10MIN.md` aloud | Outline only; **never** check the box |
| 15–30 min/day hand-coding habit | Tom | Not an agent deliverable |

Fixture smoke (`replay_fixture` / `bundle_kind=fixture`) remains **default**. Do not flip smoke to Option B or require Kafka/Yahoo/LangSmith for smoke.

## Candidate inventory (agent-movable)

| # | Candidate | Evidence today | Agent-movable? | Guide-sized? | Interview ROI | Notes |
|---|-----------|----------------|----------------|--------------|---------------|-------|
| **A** | **LangSmith/Phoenix real fail-open spans** | `obs/summary.py` sets `ok` from key presence only — **no SDK spans**; ARCHITECTURE §13 honesty; VISION still markets LangSmith | **Yes** | **Yes** (thin) | **Highest** | Closes largest honesty gap vs README/stack table |
| B | Guide 06 soft residuals (E3 live Compose+Yahoo demo; `rss_live` optional) | Review parked E3 as non-DoD | Yes (ops proof) | Too thin for full guide | Low | Operator note / optional probe — not Guide 07 |
| C | U4 / TRAINING_DATA hygiene (FB→META alias soft pin, MSFT/SPY coverage honesty) | U4 + 05a/05b **already landed**; alias documented as “soft pin later” | Partial | Thin / Align-level | Medium | Improves train coverage; not a new “news source” slice |
| D | Agent-on-consume (Agent 1→2 on Kafka) | ARCHITECTURE §6.2 defers; 16GB RAM risk | Yes | Large | Medium-high | Bigger than one thin guide; reopen scope carefully |
| E | Live-Ollama eval schema-pass rates | Guide 03 goldens structural only | Yes | Medium | Medium | Needs Ollama in CI story; separate from LLMOps spans |
| F | ARCHITECTURE §13 “screenshots not present” drift | Guide 02 already checked in `docs/assets/` | Docs Align only | No | Low | Catch-up Align, not Guide 07 |

## Acceptance criteria (this Gather)

- [x] Inventory of honest next **agent** slices with evidence paths  
- [x] Exactly **one** recommended Guide 07 candidate + ranked alternatives  
- [x] Human MV walkthrough / daily-prep explicitly excluded from agent DoD  
- [x] Fixture smoke default affirmed  
- [x] Open decision for human lock of Guide 07 (recommend + tradeoffs)  
- [x] No Write-dev-guide / Implement in this stage  

## In scope (Gather only)

- Rank residuals; recommend Guide 07 shape at context level  
- Soft-pin intent for Write-dev-guide (not a full guide yet)

## Out of scope

- Implement; Write-dev-guide; Align  
- Ticking VISION MV walkthrough / daily-prep boxes  
- Changing default smoke / requiring LangSmith key for smoke  
- Brokerage APIs; Lowd Capital; second LLM auditor; neural reranker  
- Fake freeze / overclaiming production risk model  

## Prior art (paths only)

- `docs/VISION.md` — Guide 06 landed; LS/Phoenix stubs called out on MV replay row; walkthrough unchecked  
- `docs/ARCHITECTURE.md` §13 — local envelope real; LS/Phoenix **status stubs**; fail-open DF-6  
- `src/alphaguard/obs/summary.py` — `best_effort_adapters` key-presence theater  
- `docs/2026-07-17_guide06_live_rss_reliability_context_summary.md` — Guide 06 closed  
- `docs/2026-07-17_guide06_live_rss_review.md` — E3 residual parked  
- `docs/TRAINING_DATA.md` — U4 + 05a/05b Review shippable; FB→META alias “later”  
- `docs/WALKTHROUGH_10MIN.md` — human rehearsal  
- `AGENTS.md` — fixture smoke; Guide 06 thin RSS  
- `INTERVIEW.md` / `GETTING_STARTED.md` — local envelope fulfills packaging until obs guide  
- `second_brain/docs/2026-07-17_hub_fanin_ag_align_pass118.md`  
- `second_brain/docs/2026-07-17_prioritize_hub_pass121.md`  

## Risks and blast radius

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| Guide 07 requires LangSmith key in CI/smoke | Flaky clone path; secret pressure | Fail-open; default smoke never needs key; mock SDK in unit tests |
| Fake “ok” without spans continues | Interview trust | Guide DoD = real span emit **or** honest `skipped`/`failed`; never claim UI screenshots without capture |
| Scope creep into agent-on-consume / full Phoenix product | Weeks + RAM | Hard out of recommended Guide 07 |
| Choosing U4 alias as Guide 07 while LS stubs remain | Leaves bigger honesty hole | Prefer A; park C as follow-on Align/thin guide |
| Treating walkthrough as agent work | False portfolio % | Explicit human-only lane above |

## Edge cases (for recommended Guide 07 — preview)

- No API key / tracing off → `skipped`; smoke green  
- Bad key / network error → `failed`; pipeline still `success` (fail-open)  
- LangSmith SDK import missing → fail-open `failed` or skip with clear log  
- Do not rewrite approve/reject on tracer failure  
- No secrets in git, README, or screenshots  

## Unknowns

| Unknown | How to resolve | Blocking Write? |
|---------|----------------|-----------------|
| Exact LangSmith Python SDK API / version for thin spans | Soft-pin in Write-dev-guide via current docs | Soft |
| Whether Phoenix must ship in same guide or stay stub | Recommend **LangSmith primary + Phoenix still stub or thin fallback** | Soft — recommend LS-first |
| Screenshot capture of real UI required in Guide 07 DoD? | Prefer optional; local envelope + span id in envelope enough for thin DoD | Soft |

## Recommended approach

**Guide 07 candidate: Thin LangSmith real fail-open spans (LLMOps honesty).**

1. Replace key-presence `ok` in `best_effort_adapters` with real SDK span/run emit when `LANGSMITH_TRACING` + key set.  
2. Keep **local run summary mandatory**; tracer failure must not flip pipeline result.  
3. Unit tests with mocked client; default smoke **without** key still green (`skipped`).  
4. Same-delivery VISION/ARCHITECTURE/INTERVIEW/AGENTS honesty: stubs → “real spans when configured.”  
5. **Out:** agent-on-consume; smoke requires LangSmith; fabricated UI screenshots; Optuna; MV checkbox ticks.

**Soft-pin next stage:** Ready-check before code → Implement Guide 07 (Write complete pass 123).

## Open decisions (human)

**Locked (hub pass 123):** Guide 07 = LangSmith real fail-open spans only; Phoenix stub stays; fixture smoke default; MV walkthrough / daily-prep human-only. No residual Write decisions.

## Evidence opened this pass

- Handoff + Prioritize pass 121 + Align fan-in pass 118  
- `docs/VISION.md`, `ARCHITECTURE.md` §13, `AGENTS.md`  
- Guide 06 context + review  
- `src/alphaguard/obs/summary.py` (stub adapters)  
- `docs/TRAINING_DATA.md` (U4/05a/05b status; FB alias later)  
- `docs/WALKTHROUGH_10MIN.md`  
- Glob: no prior `*next*` context file under `alphaguard/docs/` (this Gather creates it)

## Honest readiness

- **Write-dev-guide:** **Done** — `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`.  
- **Ready for Ready-check before code?** **Yes** (hub pre-authorized).  
- **Not ready for Implement** until Ready-check Met.  
- **Will not** tick MV walkthrough / daily-prep from any agent stage.  
- Soft-pin next: **Ready-check → Implement Guide 07**.

## QUALITY self-check (§5)

- [x] Inventory + one recommendation + tradeoffs  
- [x] Human MV lanes explicit  
- [x] Edge cases / blast radius / unknowns for recommended slice  
- [x] Findings in dated context artifact  
- [x] Spoke stayed in Gather; no Write/Implement  
- [x] Open decisions surfaced for chat mirror  
