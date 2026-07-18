# Review — AlphaGuard Guide 08 Phoenix fail-open spans (pass 152)

**Date:** 2026-07-18  
**Mode:** spoke  
**Stage:** Review implementation  
**Guide:** `docs/dev_guides/2026-07-18_dev_guide_08_phoenix_fail_open_spans.md`  
**Implement:** `e5aad97`  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_review_guide08_phoenix_pass152_handoff.md`  
**Locks:** A/A/A (`arize-phoenix-otel` + `PHOENIX_ENABLED` + `extras.phoenix_span_id`)

## Scope checked

Guide DoD vs `e5aad97`: real Phoenix/OTEL chain span when `PHOENIX_ENABLED`; `ok` only after span + `force_flush`; else `skipped`/`failed`; fail-open (decision unchanged; success+failed → `degraded`); `extras.phoenix_span_id` on `ok`; mocked unit tests; default smoke without Phoenix; LangSmith path unchanged; live operator docs honesty; Interview-prep VISION boxes unchecked.

## Locks A/A/A verification

| Lock | Evidence | Verdict |
|------|----------|---------|
| **A** Package / emit | `arize-phoenix-otel>=0.16.0` in `pyproject.toml`; `obs/phoenix_adapter.py` uses `phoenix.otel.register` + one `openinference_span_kind="chain"` span + `force_flush`; `auto_instrument=False` | **Met** |
| **A** Config gate | Attempt only when `settings.phoenix_enabled`; optional `phoenix_collector_endpoint` / `phoenix_project_name`; empty endpoint → default `http://localhost:6006/v1/traces` | **Met** |
| **A** Extras id | `PipelineService` sets `extras["phoenix_span_id"]` when id present; tests assert hex id | **Met** |
| No status theater | Stub `phoenix = "ok"` removed from `summary.py`; adapter called always for Phoenix path | **Met** |
| Fail-open | Broad `except` → `failed`; pipeline test: decision `approve`, status `degraded` | **Met** |
| Smoke skipped | Implement smoke + Review re-run path: default off → `skipped` (Implement: `obs.phoenix=skipped`) | **Met** |

## Findings

| Severity | Finding | Tied to | Action |
|----------|---------|---------|--------|
| Soft | Optional D3 live Phoenix collector probe not run | Guide D3 residual / DoD explicit non-blocker | Park — mocks prove emit contract |
| Soft | OTEL `force_flush` may return `True` even when HTTP export to a dead collector logs failures | Soft Adjust honesty / Ready residual | Park — Align notes; mocks assert `False` → `failed` |
| Soft | Historical docs (Guide 02/07, post–06 inventory, Guide 08 Gather context, Guide 08 prerequisite prose) still say “Phoenix stub” | Align-docs honesty stamp | **Closed Align pass 152** — inventory/context/Guide 08 status superseded; Guide 02/07 remain historical as-of their ship dates |
| Soft | Guide 08 header still says “Phoenix today is **status stub**” under Prerequisite | Guide status drift after Implement | **Closed Align pass 152** |

**Must-fix:** none.

## Architecture / quality

- Thin `obs/phoenix_adapter.py` (97 lines); `summary.py` (99 lines); `PipelineService` remains façade; no second orchestrator; no auto-instrument.
- Soft Adjust matches `arize-phoenix-otel==0.16.1`: keyword-only `register`, `set_global_tracer_provider=False`, `verbose=False`, chain span + `force_flush`.
- Injectability via `tracer_factory`; pipeline fail-open proven with patched emit.
- `phoenix_live` excluded by default `addopts`; smoke never sets `PHOENIX_ENABLED=true`.
- Secrets: no API key required for local gate; `.env.example` documents skip vs emit + optional collector/project.
- VISION Interview-prep walkthrough / daily-prep remain **unchecked**.
- Live operator docs (README / AGENTS / GETTING_STARTED / INTERVIEW / ARCHITECTURE §13 / VISION status / WALKTHROUGH / assets README / `.env.example`) — **no** remaining “Phoenix stub” claims (`LIVE_DOCS_CLEAN`).

## DoD checklist (review)

| Criterion | Verdict |
|-----------|---------|
| Real emit when configured (not flag-presence theater) | **Met** — tests assert `start_as_current_span` + `force_flush` |
| Phoenix off → `skipped`; smoke without collector | **Met** — unit + Implement smoke evidence |
| SDK/flush failure → `failed`; decision unchanged; may `degraded` | **Met** — unit + pipeline tests |
| `extras.phoenix_span_id` on `ok` | **Met** |
| LangSmith Guide 07 unchanged | **Met** — `test_langsmith_obs.py` still green |
| Live docs honesty; no Interview-prep invent; no secrets | **Met** |

## Verification (Review)

```text
uv run pytest tests/test_phoenix_obs.py tests/test_langsmith_obs.py -q
→ 14 passed, 2 deselected (langsmith_live, phoenix_live)
```

(Implement evidence retained: full suite 105 passed / 6 deselected; `make smoke` → `obs.langsmith=skipped obs.phoenix=skipped`.)

HEAD still at Implement commit: `e5aad97`.

## Shippable call

**Shippable as-is.** No must-fix. Soft Align residuals **closed pass 152**; D3 live probe + OTEL flush quirk remain parked.

## QUALITY §5

- [x] Findings tied to guide / quality bar / locks A/A/A  
- [x] Smallest fix set = none for ship (Align stamps only)  
- [x] Honest shippable call  
- [x] No unrelated refactors / no Align self-start  
