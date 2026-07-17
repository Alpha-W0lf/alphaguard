# Review — AlphaGuard Guide 07 LangSmith fail-open spans (pass 126)

**Date:** 2026-07-17  
**Mode:** spoke  
**Stage:** Review implementation  
**Guide:** `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Implement:** `287a82a`  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide07_review_pass126_handoff.md`  
**Hub:** `second_brain/docs/2026-07-17_hub_fanin_ag_guide07_implement_pass126.md`

## Scope checked

Guide DoD vs `287a82a`: real LangSmith Client emit when tracing+key; `ok` only after create+update; else `skipped`/`failed`; fail-open (decision unchanged; success+failed → `degraded`); mocked unit tests; default smoke without key; Phoenix stub; docs honesty; MV walkthrough/daily-prep unchecked.

## Findings

| Severity | Finding | Tied to | Action |
|----------|---------|---------|--------|
| Soft | Optional D3 live LangSmith probe not run (no operator key) | Guide D3 residual / DoD explicit non-blocker | Park — mocks prove emit contract |
| Soft | No dedicated unit for `create_run` ok then `update_run` raises → `failed` | Edge-case completeness | Park — broad `except` covers; optional Align/follow-on test |
| Soft | Post–Guide 06 inventory context still narrates “LS status stubs” in Gather prose | Historical Gather text | Align can stamp / supersede — not a code defect |
| Soft | Phoenix `try: phoenix = "ok"` remains status theater | Locked Phoenix stub | Accept — docs honest |

**Must-fix:** none.

## Architecture / quality

- Thin `obs/langsmith_adapter.py` (73 lines); `PipelineService` remains façade; no second orchestrator.
- Soft Adjust matches langsmith≥0.10: `create_run(name, inputs, run_type, id=..., project_name=..., start_time=...)` then `update_run`.
- Injectability via `client_factory` on adapter; pipeline fail-open proven with patched emit.
- `langsmith_live` excluded by default `addopts`; smoke never sets tracing.
- Secrets: key not logged; `.env.example` documents skip vs emit.
- VISION MV walkthrough / daily-prep remain unchecked.

## DoD checklist (review)

| Criterion | Verdict |
|-----------|---------|
| Real emit when configured (not key-presence theater) | **Met** — tests assert `create_run`/`update_run` called |
| Tracing off / empty key → `skipped`; smoke without key | **Met** — unit + Implement smoke evidence |
| SDK failure → `failed`; decision unchanged; may `degraded` | **Met** — pipeline test |
| `extras.langsmith_run_id` on `ok` | **Met** |
| Phoenix stub; no MV invent; no secrets | **Met** |

## Verification (Review)

```text
uv run pytest tests/test_langsmith_obs.py -q
→ 7 passed, 1 deselected (langsmith_live)
```

(Implement evidence retained: full suite 98 passed / 5 deselected; `make smoke` → `obs.langsmith=skipped`.)

## Shippable call

**Shippable as-is.** No must-fix. Next stage: **Align-docs** (status stamps / residual Gather prose) — hub authorize; do not self-start.

## QUALITY §5

- [x] Findings tied to guide / quality bar  
- [x] Smallest fix set = none (shippable)  
- [x] Honest shippable call  
- [x] No unrelated refactors / no Align self-start  
