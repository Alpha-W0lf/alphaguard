# Context: Post–Guide 06 agent-movable next-slice inventory

**Date:** 2026-07-17 · **Updated:** 2026-07-18 (Align Guide 08 pass 152)  
**Repos:** `alphaguard`  
**Status:** **Guide 08 Align Met (pass 152)** — LLMOps spans closed (LangSmith + Phoenix); docs match shipped reality  
**Mode last used:** spoke (pass 152 Align-docs Guide 08)  
**Stage:** Align-docs (complete) — Guide 08 closed; hub Prioritize for any next slice  
**Role lens:** Senior AI eng (LLMOps / interview honesty) + light DE  
**Guide 07 path:** `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Guide 08 path:** `docs/dev_guides/2026-07-18_dev_guide_08_phoenix_fail_open_spans.md`  
**Review Guide 08:** `docs/2026-07-18_guide08_phoenix_fail_open_review.md` (shippable as-is)  
**Implement Guide 08:** `e5aad97` · Review docs: `a60a417`  
**Guide 06 closed:** Align Met pass 118 (`d795005`)

## Outcome (Align pass 152 — supersedes Guide 07 “Phoenix stub” row)

| Item | Reality after Guide 08 |
|------|------------------------|
| LangSmith | **Real fail-open Client spans** when `LANGSMITH_TRACING` + non-empty key (`obs/langsmith_adapter.py`); Guide 07 Met |
| Phoenix | **Real fail-open OTEL chain spans** when `PHOENIX_ENABLED` (`obs/phoenix_adapter.py`); Guide 08 Met |
| Default smoke | Fixture / Kafka-down; `obs.langsmith=skipped` and `obs.phoenix=skipped` — **never** requires LangSmith key or Phoenix collector |
| Interview-prep VISION boxes | Still **unchecked** (human-only) |
| Soft residuals | D3 live LangSmith/Phoenix probes optional; OTEL flush quirk — parked, non-blocking |

## Outcome (Align pass 127 — historical Guide 07; Phoenix then stub)

| Item | Reality after Guide 07 (superseded for Phoenix by pass 152) |
|------|------------------------|
| LangSmith | Real fail-open Client spans — still true |
| Phoenix | Was status stub — **closed by Guide 08** |
| Default smoke | Fixture / Kafka-down; LangSmith skipped — still true (+ Phoenix skipped) |

## Problem (historical Gather — pass 121)

Guides **01–06** had shipped; the largest agent-movable honesty gap was LangSmith envelope **status theater**. Closed by Guide 07. Phoenix theater closed by Guide 08.

## Human-only lanes (do not propose ticking)

| VISION Interview-prep box | Owner | Agent action |
|---------------|-------|--------------|
| 10-min unprompted architecture walkthrough | Tom — rehearse `docs/WALKTHROUGH_10MIN.md` aloud | Outline only; **never** check the box |
| 15–30 min/day hand-coding habit | Tom | Not an agent deliverable |

Fixture smoke (`replay_fixture` / `bundle_kind=fixture`) remains **default**.

## Candidate inventory (agent-movable) — post–Guide 08

| # | Candidate | Status after Guide 08 | Notes |
|---|-----------|----------------------|-------|
| **A** | LangSmith real fail-open spans | **Done** (Guide 07 Align Met) | |
| **A2** | Phoenix real fail-open spans | **Done** (Guide 08 Align Met) | Thin `arize-phoenix-otel` chain span |
| B | Guide 06 soft residuals (E3 live Yahoo) | Parked | Optional ops proof |
| C | U4 FB→META alias / train hygiene | Open (thin) | Not blocking Option B |
| D | Agent-on-consume | Open (large) | Needs new Prioritize / handoff |
| E | Live-Ollama eval schema-pass rates | Open | Separate from LLMOps spans |
| F | ARCHITECTURE screenshots drift | **Closed** in Guide 07 Implement/Align | |

## Locked decisions

**Locked (hub pass 123+):** Guide 07 = LangSmith real fail-open spans; fixture smoke default; Interview-prep human-only.  
**Locked (Tom pass 152 A/A/A):** Guide 08 = Phoenix real fail-open spans (`arize-phoenix-otel`, `PHOENIX_ENABLED`, `extras.phoenix_span_id`).

## Soft residuals (parked)

- Optional D3 live LangSmith / Phoenix operator probes  
- Optional LangSmith `update_run`-failure unit  
- OTEL `force_flush` True-on-dead-collector quirk  
- Agent-on-consume / live-Ollama eval → need new hub Prioritize  

## Honest readiness

- **Guide 07:** Align Met. **Guide 08:** Align Met.  
- **LLMOps honesty gap (status theater) closed** for both LangSmith and Phoenix.  
- **Will not** tick Interview-prep boxes from any agent stage.  

## QUALITY self-check (§5)

- [x] Inventory outcome supersedes stale “Phoenix stub” prose  
- [x] Human Interview-prep lanes still explicit / unchecked  
- [x] Soft residuals parked  
- [x] Align-docs only — no Implement / no next-guide invent  
