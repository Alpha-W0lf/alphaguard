# Ready check before code — AlphaGuard thin polish CI + ARCH header (pass 155)

**Status:** Ready-check complete → **READY 9.0/10** — **stop; no Implement in this stage**  
**Guide:** `alphaguard/docs/dev_guides/2026-07-18_dev_guide_thin_polish_ci_arch_header.md`  
**Context:** `alphaguard/docs/2026-07-18_thin_polish_ci_arch_header_context_summary.md`  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_ready_ci_arch_polish_pass155_handoff.md`  
**Locks:** CI **A** (uv 3.12 frozen + pytest -q) · Triggers **A** (main + PRs)  
**Persistent spoke:** `0a88890e-8c9d-4101-b019-8754f212607d`

## Declare

Zoom-out Implement readiness for thin polish. **No coding.** Locks unchanged. Human authorized this Ready-check; Implement still needs an Implement stage/handoff (or explicit authorize) before coding.

## Checklist

| Question | Verdict |
|----------|---------|
| Context + guide aligned? | **Yes** — header stamp through Guide 08 + minimal GHA pytest; no smoke/Ollama; no Guide 09; matches Gather + Tom locks A/A |
| Current repo matches problem? | **Yes** — ARCHITECTURE header still Guide-06 Status / `2026-07-17`; **no** `.github/` workflows; `pyproject.toml` `addopts` already exclude live markers |
| Soft pins unambiguous? | **Yes** — workflow path, triggers, setup-uv + 3.12, `uv sync --frozen`, `pytest -q`, Status wording soft-pin, Soft Adjust `libgomp1` / frozen fallback bounded |
| Blast radius / rollback clear? | **Yes** — touch `ARCHITECTURE.md` header (2 lines), add `.github/workflows/ci.yml`, optional README one-liner. Rollback = revert those files |
| Edge cases planned? | **Yes** — fork PRs no secrets; live markers stay deselected; OpenMP Soft Adjust; frozen Soft Adjust; no smoke |
| Docs honesty / Interview-prep? | **Yes** — optional README CI line; Interview-prep boxes not to be checked |
| Refinements still required before Implement? | **No material** — residuals are Soft Adjust at first CI run |

## Soft residuals (non-blocking)

| Item | Note |
|------|------|
| XGBoost / OpenMP on `ubuntu-latest` | Soft Adjust `apt-get install -y libgomp1` if first CI fails |
| `uv sync --frozen` tooling mismatch | Soft Adjust to `uv sync` only if frozen fails; document |
| Exact `astral-sh/setup-uv` major tag | Soft Adjust `@v5` vs current major if marketplace differs |
| Cold-CI network/HF in a forgotten test | Unlikely (fixtures dominate); quarantine/skip if seen — escalate, do not invent Guide 09 |
| First Actions green run | Guide D3 residual — YAML correct = DoD; operator confirm optional |

## Locks confirmed (do not reopen)

| Lock | Value |
|------|--------|
| CI Python / uv | **A** — `astral-sh/setup-uv` + Python **3.12** + `uv sync --frozen` + `uv run pytest -q` |
| Triggers | **A** — push `main` + `pull_request` |
| Smoke / Ollama in CI | Forbidden |
| Live markers | Never set `ALPHAGUARD_RUN_*` in workflow |
| ARCHITECTURE | Header Status + Last Updated only |
| Out | Agent-on-consume, Guide 09 invent, matrix/Codecov as DoD |

## Implement readiness (numeric)

| Track | Score | READY? | Why not 10 |
|-------|-------|--------|------------|
| **Thin polish — CI + ARCHITECTURE header** | **9.0 / 10** | **Yes — READY** | (1) Ubuntu OpenMP/`libgomp` need unproven until first Actions run — Soft Adjust bounded; (2) `uv sync --frozen` may Soft Adjust on runner; (3) cold-CI network surprise in a forgotten test is residual (unlikely) |

**Overall call:** **READY** for Implement pending Implement-stage handoff / authorize. **This stage does not Implement.**

## Remaining human / hub gate

Await **Implement** stage handoff (or explicit “Authorize Implement thin polish CI + ARCH”). Do **not** start coding in Ready-check. Do **not** reopen locks A/A.

## Stop

Ready-check complete. **No Implement in this stage.**

## QUALITY self-check (§5)

- [x] Explicit READY + reasons  
- [x] Numeric 0–10 + why not 10  
- [x] Non-blocking residuals listed  
- [x] No implementation started  
- [x] Context ↔ guide ↔ repo evidence checked (stale header; no `.github/`)  
- [x] Locks confirmed unchanged  
