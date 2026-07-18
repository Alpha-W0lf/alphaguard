# Context: Thin polish — ARCHITECTURE header stamp + minimal GHA pytest CI

**Date:** 2026-07-18  
**Repos:** `alphaguard`  
**Status:** Draft (Gather Met) — ready for thin Write-dev-guide  
**Mode last used:** spoke (Gather pass 155)  
**Stage:** Gather context  
**Role lens:** Senior DE / portfolio ops (CI signal) + docs honesty  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_gather_ci_arch_polish_pass155_handoff.md`  
**Hub:** `second_brain/docs/2026-07-18_prioritize_hub_pass155.md`  
**Quality:** `second_brain/docs/2026-07-18_portfolio_quality_assessment_pass155.md` (AG DE/ops 7/10 — **no CI workflows**; ARCHITECTURE header date lag)

## Problem

AlphaGuard **build MV is Met** (guides 01–08 closed; Guide 08 Align `ecefe29`). Two thin honesty/portfolio gaps remain:

1. **`docs/ARCHITECTURE.md` header lag** — body already documents Guide 07/08 LLMOps, but header still says Status through Guide **06** and **Last Updated: 2026-07-17 (Align Guide 06)**. Clone reviewers / interviewers who skim the header get a stale “how far did we ship?” signal.  
2. **No GitHub Actions workflows** — `Glob **/.github/**/*` → **0 files**. Default `uv run pytest -q` already excludes live markers (`kafka_integration`, `rss_live`, `langsmith_live`, `phoenix_live`) and collects **105/111** tests without Ollama/Kafka/Yahoo. Pass 155 quality audit flags missing CI as the biggest DE/ops portfolio gap.

This is **polish**, not a feature Guide 09.

## Acceptance criteria

- [ ] `ARCHITECTURE.md` header **Status** + **Last Updated** honestly reflect guides **01–08** closed / Guide 08 Align Met (Phoenix real fail-open; fixture smoke default)  
- [ ] Minimal GitHub Actions workflow runs `uv run pytest -q` on ubuntu (default `addopts` already exclude live markers)  
- [ ] CI does **not** require Ollama, Kafka, Yahoo, LangSmith key, or Phoenix collector  
- [ ] CI does **not** run `make smoke` (host Ollama path)  
- [ ] No agent-on-consume / no Guide 09 feature invent  
- [ ] Thin same-delivery honesty: mention CI in README or GETTING_STARTED if one line is enough (optional but preferred)  
- [ ] Interview-prep VISION boxes remain unchecked  

## In scope

1. Stamp `docs/ARCHITECTURE.md` header (Status + Last Updated; do **not** rewrite contracts).  
2. Add `.github/workflows/ci.yml` (or equivalent) — checkout → Python/`uv` → sync → `uv run pytest -q`.  
3. Context → thin Write → (Ready) → Implement for this polish only.

## Out of scope

- Agent-on-consume / 24/7 RSS / live-Ollama eval rates  
- Inventing Guide 09 product features  
- Multi-OS matrix / coverage badges / Codecov / Dependabot as DoD  
- Running Kafka Compose or `make smoke` in CI  
- Requiring secrets in GitHub Actions  
- Mechanic/Vehicle/AI KB work  

## Prior art (paths only)

| Path | Why |
|------|-----|
| `docs/ARCHITECTURE.md` L1–7 | Stale Status/Last Updated vs Guide 08 body |
| `docs/ARCHITECTURE.md` §2 / §13 | Already honest on Guide 07/08 LLMOps |
| `docs/2026-07-18_guide08_align_docs.md` | Guide 08 slice closed evidence |
| `pyproject.toml` `[tool.pytest.ini_options]` | Default `addopts` exclude live markers |
| `.python-version` | `3.12` |
| Quality pass 155 | AG: stamp ARCH + minimal GHA pytest |
| Hub pass 155 | Ordered AG polish = Gather → Write (thin) |
| Guide 01 | Explicitly deferred “CI on GitHub Actions (nice-to-have)” — now unlock |
| `mechanic_rag/.github/workflows/ci.yml` | Thin prior art shape (different stack; pattern only) |

## Risks and blast radius

| Risk | Angle | Mitigation |
|------|-------|------------|
| Heavy deps (`sentence-transformers`, `transformers`, `xgboost`) slow/fail CI | Clone/PR latency; OOM | Soft-pin: single ubuntu job; cache `uv`; timeout budget; do **not** download HF models in default tests (fixtures only — verify in Write if any test hits network) |
| Accidental live marker enable | Flaky CI | Rely on existing `addopts`; never set `ALPHAGUARD_RUN_*` in workflow |
| `make smoke` in CI | Needs Ollama → red forever | Explicitly out |
| Over-editing ARCHITECTURE body | Contract churn | Header stamp only (+ maybe one Status clause); §13 already correct |
| Docs claim “CI green” without workflow | Honesty | Same-delivery workflow file + optional README one-liner |

## Edge cases

| Case | Required behavior |
|------|-------------------|
| PR from fork | Workflow runs without secrets |
| Live-marked tests present | Deselected by default `addopts` (6 deselected locally) |
| `uv.lock` drift | Prefer `uv sync --frozen` (or document Soft Adjust if frozen fails on runner) |
| macOS libomp vs Linux | Default unit tests must not require brew libomp; if XGBoost fails on ubuntu, Soft Adjust pin OpenMP/`libgomp` apt — verify at Implement |
| Header stamp only vs deep Status rewrite | Prefer concise Status listing guides 01–08 Met + fixture smoke default |

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking? |
|---------|----------------|-----------|
| Whether any default pytest path downloads models / hits network on cold CI | Spot-check tests for HF/yfinance network at Write/Implement; fail closed if so | Soft — likely OK (fixtures dominate) |
| XGBoost / OpenMP on `ubuntu-latest` without brew | First CI run Soft Adjust (`apt-get install libgomp1` if needed) | Soft |
| Exact Status one-liner wording | Soft-pin in Write | No |

## Recommended approach

**Trivially thin polish** — Write-dev-guide can be a short checklist (justify: two files, no product contracts). Soft pins:

1. **ARCHITECTURE header:** Update **Status** to binding SSOT through Guide **08** Align Met (LangSmith + Phoenix real fail-open; default smoke fixture). **Last Updated:** `2026-07-18 (Align Guide 08 + CI polish)` or Implement date when landed.  
2. **Workflow:** `.github/workflows/ci.yml`  
   - triggers: `push` to `main` + `pull_request`  
   - `actions/checkout@v4`  
   - `astral-sh/setup-uv` + Python **3.12** (match `.python-version`)  
   - `uv sync --frozen` (dev/pytest available)  
   - `uv run pytest -q`  
   - **No** env for live markers; **no** smoke  
3. Optional: README “CI” one-liner under Evidence / Limitations.  
4. Stop. No feature guides.

## Open decisions (human)

### Decision: CI Python / uv setup

- **Plain title:** How should GitHub Actions install Python and deps?
- **In plain terms:** Match local `uv` + 3.12 without inventing a second package manager story.
- **Options:**  
  - **A** — `astral-sh/setup-uv` + Python 3.12 + `uv sync --frozen` (recommended)  
  - **B** — `actions/setup-python` + pip install editable  
  - **C** — Python version matrix 3.11 + 3.12
- **Recommendation:** **A**
- **Reasoning:** Matches repo tooling (`uv.lock`, `.python-version`); single job keeps polish thin. Matrix is nice later, not DoD.
- **Tradeoffs:** A ties CI to uv (already project SSOT). C doubles minutes. B drifts from local path.
- **Needs from you:** Lock A (or B/C).

### Decision: Workflow triggers

- **Plain title:** When should CI run?
- **Options:** **A** push `main` + all PRs · **B** PRs only · **C** manual `workflow_dispatch` only
- **Recommendation:** **A**
- **Reasoning:** Standard portfolio signal; catches main-direct pushes.
- **Tradeoffs:** A uses more minutes than B. C is too weak for “has CI” claim.
- **Needs from you:** Lock A unless minutes are a concern → B.

### Decision: Is a full Write-dev-guide required?

- **Plain title:** Next stage shape for this polish?
- **Options:** **A** Thin Write-dev-guide then Ready-check · **B** Skip Write; Ready-check from this context alone · **C** Implement immediately after Gather
- **Recommendation:** **A** (thin Write)
- **Reasoning:** Workflow OS still wants an executable checklist; change is small enough that Write is ≤1 short guide. C skips Ready gate.
- **Tradeoffs:** A adds one short stage. B faster but weaker handoff for Implement agent.
- **Needs from you:** Prefer A unless hub says Ready-from-Gather.

## Evidence opened this pass

- Handoff pass 155; hub Prioritize pass 155; quality assessment pass 155  
- `docs/ARCHITECTURE.md` header vs §2/§13 Guide 08 body  
- `pyproject.toml` pytest markers / `addopts`  
- `.python-version` = `3.12`  
- `Glob **/.github/**/*` → empty  
- `uv run pytest --collect-only -q` → **105/111 collected (6 deselected)**  
- Guide 01 deferred CI note; Guide 08 Align closed  
- `mechanic_rag` CI as pattern-only prior art  

## Honest readiness

- **Gather DoD:** Met.  
- **Ready for Write-dev-guide?** **Yes** — thin guide justified (header stamp + one workflow file).  
- **Not ready for Implement** until Write (+ Ready-check / standing authorize).  
- **Will not** invent agent-on-consume or Guide 09 features.

## QUALITY self-check (§5)

- [x] Assumptions listed as soft pins / open decisions  
- [x] Edge cases + blast radius (≥2 angles: CI flake, ARCH contract churn)  
- [x] Findings written to this artifact + handoff Results  
- [x] Spoke stayed in thin polish slice; no Implement  
- [x] Open decisions surfaced with recommendation + reasoning + tradeoffs  
