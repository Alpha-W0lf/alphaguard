# Context: Post–Guide 06 agent-movable next-slice inventory

**Date:** 2026-07-17  
**Repos:** `alphaguard`  
**Status:** **Guide 07 Align Met (pass 127)** — slice closed; docs match shipped reality  
**Mode last used:** spoke (pass 127 Align-docs)  
**Stage:** Align-docs (complete) — Guide 07 closed; hub Prioritize for any Guide 08  
**Role lens:** Senior AI eng (LLMOps / interview honesty) + light DE  
**Guide 07 path:** `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Review:** `docs/2026-07-17_guide07_langsmith_fail_open_review.md` (shippable as-is)  
**Implement:** `287a82a` · Review docs: `1200da6`  
**Align handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide07_align_pass127_handoff.md`  
**Guide 06 closed:** Align Met pass 118 (`d795005`)

## Outcome (Align pass 127 — supersedes Gather “stubs” prose)

| Item | Reality after Guide 07 |
|------|------------------------|
| LangSmith | **Real fail-open Client spans** when `LANGSMITH_TRACING` + non-empty key (`obs/langsmith_adapter.py`); `ok` only after emit; else `skipped`/`failed`; `extras.langsmith_run_id` on success |
| Phoenix | **Status stub** remains (no real Phoenix spans) — honesty required |
| Default smoke | Fixture / Kafka-down; `obs.langsmith=skipped` — **never** requires LangSmith key |
| MV walkthrough / daily-prep | Still **unchecked** (human-only) |
| Soft residuals | D3 live probe optional; optional update_run-failure unit — parked, non-blocking |

## Problem (historical Gather — pass 121)

Guides **01–06** had shipped; the largest agent-movable honesty gap was LangSmith envelope **status theater** (key presence → `ok` without spans). That gap is **closed** by Guide 07. Portfolio doneness remains capped by **human** VISION MV boxes — agents must **not** tick those.

## Human-only lanes (do not propose ticking)

| VISION MV box | Owner | Agent action |
|---------------|-------|--------------|
| 10-min unprompted architecture walkthrough | Tom — rehearse `docs/WALKTHROUGH_10MIN.md` aloud | Outline only; **never** check the box |
| 15–30 min/day hand-coding habit | Tom | Not an agent deliverable |

Fixture smoke (`replay_fixture` / `bundle_kind=fixture`) remains **default**.

## Candidate inventory (agent-movable) — post–Guide 07

| # | Candidate | Status after Guide 07 | Notes |
|---|-----------|----------------------|-------|
| **A** | LangSmith real fail-open spans | **Done** (Guide 07 Align Met) | Phoenix stub deferred |
| B | Guide 06 soft residuals (E3 live Yahoo) | Parked | Optional ops proof |
| C | U4 FB→META alias / train hygiene | Open (thin) | Not blocking Option B |
| D | Agent-on-consume | Open (large) | Needs new Prioritize / handoff |
| E | Live-Ollama eval schema-pass rates | Open | Separate from LLMOps spans |
| F | ARCHITECTURE screenshots drift | **Closed** in Guide 07 Implement/Align (§13 assets present) | |

## Acceptance criteria (this Gather) — historical

- [x] Inventory of honest next **agent** slices with evidence paths  
- [x] Exactly **one** recommended Guide 07 candidate + ranked alternatives  
- [x] Human MV walkthrough / daily-prep explicitly excluded from agent DoD  
- [x] Fixture smoke default affirmed  
- [x] Open decision for human lock of Guide 07 (recommend + tradeoffs)  
- [x] No Write-dev-guide / Implement in this stage  

## Locked decisions

**Locked (hub pass 123+):** Guide 07 = LangSmith real fail-open spans only; Phoenix stub stays; fixture smoke default; MV walkthrough / daily-prep human-only.

## Soft residuals (parked)

- Optional D3 live LangSmith operator probe  
- Optional unit: `create_run` ok then `update_run` raises → `failed`  
- Phoenix real spans → future guide only after new hub Prioritize  

## Honest readiness

- **Guide 07 lifecycle:** Gather → Write → Ready-check (9.0) → Implement → Review (shippable) → **Align Met**.  
- **Slice closed.** Do **not** start Guide 08 without new hub Prioritize + handoff.  
- **Will not** tick MV walkthrough / daily-prep from any agent stage.  

## QUALITY self-check (§5)

- [x] Inventory outcome supersedes stale “stubs” Gather prose  
- [x] Human MV lanes still explicit / unchecked  
- [x] Soft residuals parked with owners (optional / future Prioritize)  
- [x] Align-docs only — no Implement / no Guide 08 start  
