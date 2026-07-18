# Dev Guide — Thin polish: ARCHITECTURE header + minimal GHA pytest CI

**Date:** 2026-07-18  
**Repo:** `alphaguard`  
**Work item:** Thin polish — ARCHITECTURE header stamp + minimal GitHub Actions `pytest`  
**Stage that authored this:** Write-dev-guide (pass 155)  
**Status:** **Draft / Write Met** — ready for Ready-check; **no Implement yet**  
**Justify thin guide:** Two touch surfaces (header stamp + one workflow file); no product contract changes; Gather already locked soft pins.

**Context SSOT:** `alphaguard/docs/2026-07-18_thin_polish_ci_arch_header_context_summary.md`  
**Hub:** `second_brain/docs/2026-07-18_prioritize_hub_pass155.md`  
**Write handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_write_ci_arch_polish_pass155_handoff.md`  
**Prerequisite:** Guides 01–08 Align Met (build MV Met). Default smoke still fixture / Kafka-down.

**Human locks (pass 155 — do not reopen):**

| Lock | Value |
|------|--------|
| CI Python / uv | **A** — `astral-sh/setup-uv` + Python **3.12** + `uv sync --frozen` + `uv run pytest -q` |
| Triggers | **A** — `push` to `main` + `pull_request` |
| Smoke / Ollama in CI | **Forbidden** |
| Live markers | Never set `ALPHAGUARD_RUN_*` in workflow; rely on `pyproject.toml` `addopts` |
| Scope | Header stamp + minimal CI only — **no** agent-on-consume / Guide 09 invent |
| Interview-prep VISION boxes | **Human-only** — do not invent ticks |

---

## Objective

Close two portfolio honesty gaps after Guide 08:

1. Stamp `docs/ARCHITECTURE.md` header so Status / Last Updated match shipped guides **01–08** (body already honest).  
2. Add minimal GitHub Actions CI that runs the same default unit suite reviewers run locally (`uv run pytest -q`), proving clone/PR green without Ollama/Kafka/secrets.

**Success signal:** Header no longer claims “through Guide 06 only”; `.github/workflows/ci.yml` exists and would run pytest with live markers deselected; local `uv run pytest -q` still green; no smoke in CI.

---

## Learning notes (new for this polish)

1. **Header vs body drift** — Skim readers trust Status/Last Updated; body §13 can be correct while the header lies.  
2. **CI = default test selection** — Portfolio CI should match `addopts`, not invent a second suite.  
3. **Fail closed on live deps** — Never put `make smoke` or live markers in CI; that turns optional ops into red-main theater.

---

## References (paths only)

- `alphaguard/docs/2026-07-18_thin_polish_ci_arch_header_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (header L1–7; do not reopen § contracts)
- `alphaguard/docs/2026-07-18_guide08_align_docs.md`
- `alphaguard/pyproject.toml` (`addopts` live-marker exclusions)
- `alphaguard/.python-version` (`3.12`)
- `alphaguard/uv.lock`
- `alphaguard/README.md` (optional one-liner)
- `second_brain/docs/2026-07-18_portfolio_quality_assessment_pass155.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **Header stamp only** for ARCHITECTURE — no AG1–AG3 reopen; no § rewrite beyond Status/Last Updated lines.  
2. **Single ubuntu job** — no OS matrix, no Codecov, no Dependabot as DoD.  
3. **No secrets** in Actions; fork PRs must run.  
4. **No** `make smoke`, Compose Kafka, Yahoo, LangSmith key, Phoenix collector.  
5. Prefer ≤300 lines for workflow YAML (will be tiny).  
6. Soft Adjust allowed: if XGBoost needs OpenMP on ubuntu, add `sudo apt-get install -y libgomp1` **before** pytest — do not expand scope.  
7. Soft Adjust: if `uv sync --frozen` fails on runner due to lock tooling mismatch, document and use `uv sync` only after noting Adjust — prefer frozen first.

---

## Soft pins (locked)

| Pin | Locked default |
|-----|----------------|
| Workflow path | `.github/workflows/ci.yml` |
| `on` | `push: branches: [main]` + `pull_request:` |
| Job | `runs-on: ubuntu-latest`; name e.g. `pytest` |
| Checkout | `actions/checkout@v4` |
| uv | `astral-sh/setup-uv@v5` (or current major) with `python-version: "3.12"` (or `enable-cache: true` if supported) |
| Install | `uv sync --frozen` (include project + pytest via uv dev-deps / project) |
| Test | `uv run pytest -q` |
| Env | Do **not** set `ALPHAGUARD_RUN_KAFKA_TESTS`, `ALPHAGUARD_RUN_RSS_LIVE`, `ALPHAGUARD_RUN_LANGSMITH_LIVE`, `ALPHAGUARD_RUN_PHOENIX_LIVE` |
| ARCH Status (soft wording) | Binding contracts SSOT — guides **01–08** landed (incl. Guide 07 LangSmith + Guide 08 Phoenix real fail-open spans); default smoke still `bundle_kind=fixture` |
| ARCH Last Updated | `2026-07-18` (CI polish / Guide 08 header stamp) — Implement may use commit day if later |
| README | Prefer one Evidence/Limitations line: “GitHub Actions runs default `uv run pytest -q` (live markers excluded)” |

### Suggested Status line (Implement may Soft Adjust wording, not meaning)

```text
**Status:** Binding contracts SSOT — guides 01–08 landed (05a/05b Option B lab; 06 thin RSS; 07 LangSmith + 08 Phoenix real fail-open spans); default smoke still `bundle_kind=fixture`
```

### Suggested workflow skeleton (Implement fills exact action versions)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run pytest -q
```

---

## Acceptance criteria (Implement must meet)

- [ ] `ARCHITECTURE.md` Status + Last Updated reflect guides 01–08 / Guide 08 honesty (not Guide 06-only)  
- [ ] `.github/workflows/ci.yml` present with locks A/A (uv 3.12 frozen + pytest -q; push main + PRs)  
- [ ] Workflow does not run smoke / does not enable live markers  
- [ ] Local `uv run pytest -q` still green after changes  
- [ ] Optional README CI one-liner  
- [ ] No Interview-prep VISION ticks; no Guide 09 invent; no agent-on-consume  

---

## Ordered step checklist

### Phase A — ARCHITECTURE header

- [ ] **A1.** Edit only header **Status** + **Last Updated** (soft wording above).  
- [ ] **A2.** Grep header for “Guide 06” / stale Last Updated; confirm body §2/§13 unchanged unless already correct.

### Phase B — GitHub Actions

- [ ] **B1.** Create `.github/workflows/ci.yml` per soft pins.  
- [ ] **B2.** Do not add secrets, matrix, smoke, or `ALPHAGUARD_RUN_*`.  
- [ ] **B3.** Soft Adjust only if needed: `libgomp1` apt before pytest.

### Phase C — Docs honesty + stop

- [ ] **C1.** Optional README one-liner for CI.  
- [ ] **C2.** Grep claim “no CI” if any live operator docs say that; fix thinly.  
- [ ] **C3.** Stop. No feature work.

### Phase D — Verification

- [ ] **D1.** `uv run pytest -q` green locally.  
- [ ] **D2.** Confirm workflow file parses (YAML present; triggers correct).  
- [ ] **D3.** Optional: after push, confirm Actions run appears (operator residual if minutes lag — not DoD blocker if file correct).

---

## Verification / Definition of Done

**Done when all are true:**

1. ARCHITECTURE header Status/Last Updated honest through Guide 08.  
2. Minimal GHA workflow exists and matches Tom locks A/A.  
3. Default pytest path unchanged (live markers still excluded).  
4. No smoke/Ollama/secrets in CI.  
5. No Guide 09 / agent-on-consume invent; Interview-prep boxes untouched.

**Explicitly not required:**

- Green Actions badge screenshot  
- Multi-version matrix  
- Coverage / Codecov  
- `make smoke` in CI  
- First Actions run must finish before DoD if YAML correct (D3 residual OK)

**Suggested verification commands:**

```bash
# From alphaguard/
uv run pytest -q
# Inspect:
#   head -n 8 docs/ARCHITECTURE.md
#   cat .github/workflows/ci.yml
```

---

## Blast radius and risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| XGBoost OpenMP missing on ubuntu | Red CI | Soft Adjust `libgomp1` |
| Frozen sync fails | Red CI | Soft Adjust document → `uv sync` |
| Header over-edit | Contract confusion | Status/Last Updated only |
| Accidental smoke in CI | Permanent red | Stop list + review |
| Heavy HF download in a forgotten test | Slow/flake CI | If seen at Implement, quarantine/skip — escalate; do not invent Guide 09 |

---

## Edge-case handling

| Case | Required behavior |
|------|-------------------|
| Fork PR | Runs without secrets |
| Live-marked tests | Remain deselected via `addopts` |
| `uv.lock` out of date | Commit lock with dep changes only if Soft Adjust requires; prefer frozen |
| Stale “Guide 06” in Status | Must be gone after A1 |

---

## Out of scope (stop list)

- Implement in this Write stage  
- Agent-on-consume / Guide 09 features  
- Kafka Compose / smoke / live markers in CI  
- OS matrix / Codecov / Dependabot as DoD  
- Interview-prep VISION checkbox invent  
- Mechanic / Vehicle / AI KB  

---

## Honest readiness

- **Write-dev-guide:** Met — thin executable guide; Tom locks A/A/A frozen.  
- **Ready for Ready-check before code?** Yes.  
- **Not ready for Implement** until Ready-check / authorize.  
- **Will not** invent Guide 09 or agent-on-consume.

## QUALITY self-check (§5)

- [x] Steps, DoD, blast radius, edge cases present  
- [x] Locks frozen; Soft Adjust bounded  
- [x] No code implemented this stage  
- [x] Spoke stayed in thin polish slice  
