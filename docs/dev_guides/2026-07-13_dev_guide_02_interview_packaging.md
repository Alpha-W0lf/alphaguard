# Dev Guide 02 — Interview packaging

**Date:** 2026-07-13  
**Repo:** `alphaguard`  
**Work item:** Guide 02 — interview packaging (FAQ, clone path, README diagram, local-envelope screenshots)  
**Stage that authored this:** Write → Refine-dev-guide (pass 17)  
**Status:** Implement DoD met (pass 22); Review complete — shippable as-is (pass 23)

**Context SSOT:** `alphaguard/docs/2026-07-13_guide02_interview_packaging_context_summary.md`  
**Prerequisite:** Guide 01 vertical slice is shippable (pass-9). This guide adds **docs + assets only** — no pipeline/product code.

---

## Objective

Land the **defendable interview shell** around the already-green replay smoke:

1. Root `INTERVIEW.md` — ≥15 gotcha Q&A covering the themes in Acceptance Criteria below.  
2. Root `GETTING_STARTED.md` — clean-clone path (Python 3.12 / `uv` / `gemma4:e2b` / `make bundle` / `make smoke` with Kafka down).  
3. README polish — simplified ARCHITECTURE §4 mermaid + stack table; still **vertical slice / not v1 complete**.  
4. `docs/assets/` — ≥2 checked-in screenshots (terminal smoke + curated envelope JSON) with redaction + LS/Phoenix stub honesty.  
5. Operator honesty pass — default `gemma4:e2b`, fixture≠Option B, local envelope fulfills packaging until H2 reversed.

**Success signal:** A reviewer can clone, follow GETTING_STARTED, run smoke, open INTERVIEW.md, and see honest local LLMOps evidence without needing Kafka, Option B train, or real LangSmith/Phoenix UI.

---

## Learning notes (new for this guide)

1. **Packaging vs vertical slice** — Guide 01 proved the **critical path works** (fixture → PipelineService → agents → local envelope). Packaging is the **interview shell**: FAQ, clone path, diagram, screenshots. It does not add Kafka maturity or Option B training proof. Treat packaging as a separate deliverable so status theater (“v1 Done”) does not sneak in with docs.

2. **Deterministic gate vs stochastic proposer** — Agent 1’s `BUY|HOLD|PASS` is LLM-sampled; Agent 2’s policy map is fixed. The same fixture event can show `BUY`+reject or `HOLD`+approve across runs while the gate rules stay identical. Screenshots and FAQ must teach that variance is expected — do not chase a “golden” proposal image.

3. **Evidence redaction** — A true local envelope can still be unsafe to commit as a PNG if it embeds absolute home paths (`obs.local_summary_path`). Portfolio artifacts need a **redaction checklist**, not only a “don’t fake LangSmith” rule.

4. **Architecture sequence ≠ interview ROI order** — ARCHITECTURE §15 lists packaging after Kafka/Option B as a dependency sketch. Pass-12 **soft-overrides** that for interview ROI because packaging needs only the green vertical slice. This guide cites that override explicitly so Implement does not “correct” back to Kafka-first.

---

## References (paths only)

### Product / contracts / rails

- `alphaguard/docs/VISION.md`
- `alphaguard/docs/ARCHITECTURE.md` (§4 mermaid; §13 obs; §15 sequencing; §16 resource modes)
- `alphaguard/README.md`
- `alphaguard/AGENTS.md`
- `alphaguard/Makefile`
- `alphaguard/.env.example`
- `alphaguard/.python-version`
- `alphaguard/.gitignore`
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md`
- `alphaguard/docs/2026-07-13_guide02_interview_packaging_context_summary.md`

### Program / soft override evidence

- `second_brain/docs/2026-07-13_alphaguard_prioritize_next_work_pass12.md`
- `second_brain/docs/2026-07-13_prioritize_next_work_pass12_fan_in.md`
- `second_brain/docs/2026-07-13_alphaguard_review_impl_pass9.md`
- `second_brain/docs/2026-07-13_alphaguard_align_docs_pass10.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

### Runtime evidence sources (for screenshots / FAQ claims — do not git-add raw tree)

- `alphaguard/data/fixtures/` (incl. `model_bundle_fixture/manifest.json`)
- `alphaguard/artifacts/runs/*.json` (gitignored; source for curated PNGs)
- `alphaguard/tests/test_gate.py`
- `alphaguard/eval/golden_cases.jsonl`

---

## Architecture constraints (binding)

1. **Docs + assets only.** No pipeline features, no Kafka producer/consumer, no Option B train, no real LangSmith/Phoenix SDK wiring, no neural reranker, no brokerage / Lowd Capital.  
2. **AG1–AG3 locked** — FAQ paraphrases ARCHITECTURE; does not soften contracts. ARCHITECTURE wins on any wording conflict.  
3. **Replay-first packaging story:** default demo = `ALPHAGUARD_MODE=replay` + `ALPHAGUARD_RAG_MODE=fixture` + `resource_mode=replay_fixture`. Kafka Compose may exist; smoke **must not require** Kafka up.  
4. **Fixture ≠ Option B:** `bundle_kind=fixture` proves plumbing. Never quote `metrics.train_f1_at_threshold=1.0` (synthetic `n_rows=64`) as model quality.  
5. **LLMOps honesty (ARCHITECTURE §13):** local run summary is mandatory and real; `obs.langsmith` / `obs.phoenix` are **status stubs**. Screenshots prove the local envelope — **not** fabricated LangSmith/Phoenix UI.  
6. **VISION Sharing Strategy vs H2:** local envelope screenshots **fulfill packaging intent** until H2 is reversed. Captions must say LS/Phoenix are stubs. Do not invent UI to match the literal VISION row.  
7. **Packaging-first soft override of ARCHITECTURE §15:** pass-12 + hub Band B prioritize packaging before Kafka E2E / Option B for interview ROI. Contracts unchanged; sequencing text is soft-overridden for this work item. Do **not** silently rewrite VISION MV checkboxes in this guide’s Implement — Align-docs owns checkbox updates after evidence exists.  
8. **Gemma default honesty:** `OLLAMA_MODEL=gemma4:e2b` needs current Ollama; **412** → upgrade or fallback `qwen3.5:4b`. Do not claim gemma works without pull/smoke evidence; do not reintroduce “qwen-only DoD.”  
9. **Paths pinned:** `INTERVIEW.md` and `GETTING_STARTED.md` at **repo root**. Screenshots under `docs/assets/`. `artifacts/` stays gitignored. Never commit `.env`.  
10. **LICENSE** and **Compose healthcheck appendix** are **out of this guide’s core DoD** (follow-on / Kafka guide).  
11. Still say **vertical slice / not v1 complete** in README and operator docs.  
12. Prefer ≤300 lines/file for any incidental doc edits; no new product modules.

---

## Acceptance criteria (Implement must meet)

Copied/refined from context SSOT — do not invent extra scope:

- [x] `INTERVIEW.md` at repo root with **≥15** gotcha Q&A covering themes listed in Phase A  
- [x] `GETTING_STARTED.md` at repo root with clean-clone path (see Phase B)  
- [x] README gains architecture mermaid (simplify ARCHITECTURE §4) + stack table; still vertical slice / not v1 complete; fixture ≠ Option B  
- [x] `docs/assets/` has **≥2** checked-in screenshots: (1) terminal smoke, (2) curated envelope JSON — LS/Phoenix stub captions; home paths redacted; Agent 1 variance caption  
- [x] Operator docs keep default `gemma4:e2b` honesty (412 / fallback)  
- [x] No new pipeline features; no Kafka E2E; no Option B train; no real LS/Phoenix SDK; LICENSE not required in core DoD  
- [x] Do not silently tick VISION MV boxes without Align-docs evidence pass  
- [x] FAQ / captions reconcile VISION “LangSmith screenshots” wording via local-envelope fulfillment until H2 reversed  

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — `INTERVIEW.md` (≥15 gotcha Q&A)

**Tone (pinned soft default):** Concise staff-interview FAQ — short question, 2–6 sentence answer, point to ARCHITECTURE / tests for contracts. Prefer “gotcha + why we chose X” over essay. Cap ~15–25 questions. Tradeoff: denser FAQ is faster for drills; longer essays drift and contradict ARCHITECTURE.

- [x] **A1.** Create `alphaguard/INTERVIEW.md` at **repo root** (not under `docs/`).  
- [x] **A2.** Write **≥15** Q&A covering **all** required themes below. Exact question wording may be drafted in Implement; titles below are the checklist. Each theme must appear at least once (one Q may cover a tightly related pair if both ideas are explicit in the answer).

**Required themes + example Q titles (Implement drafts full answers):**

| # | Theme (must cover) | Example Q title (wording flexible) |
|---|--------------------|-------------------------------------|
| 1 | AG1 actions / no `SELL` | Why only `BUY\|HOLD\|PASS` — why reject `SELL`? |
| 2 | AG1 gate policy map | How does the gate map `(action, downside_risk_score)` → approve/reject? |
| 3 | AG2 label honesty | What is the learned label, and why never OR volatility into it? |
| 4 | AG3 as-of / leakage | How does unified as-of prevent look-ahead leakage in RAG hits? |
| 5 | Gate: `BUY` vs `HOLD`/`PASS` | Why can `HOLD`/`PASS` approve while `BUY` rejects at the same score? |
| 6 | Fixture ≠ Option B | Why must we not cite fixture `train_f1_at_threshold=1.0` as model quality? |
| 7 | Replay vs Kafka | What does replay-first prove vs what Kafka E2E still needs to prove? |
| 8 | Resource modes | What is `replay_fixture` vs `kafka_integration` (ARCHITECTURE §16)? |
| 9 | Ollama / `gemma4:e2b` honesty | What happens on old Ollama 412, and what is the documented fallback? |
| 10 | Identity ownership | Who owns `event_id`/`ticker` if the LLM returns different values? |
| 11 | LS/Phoenix stubs vs local envelope | Are LangSmith/Phoenix “wired,” and what is the real LLMOps baseline? |
| 12 | Agent 1 non-determinism vs deterministic gate | Why can the same event show `BUY` or `HOLD` across smokes? |
| 13 | Compose ≠ Kafka maturity | Does `docker-compose.yml` prove Kafka delivery contracts? |
| 14 | Out-of-universe / fail-closed | What happens to an out-of-universe ticker or invalid proposal? |
| 15 | Eval / invariants location | Where do unit tests vs golden stubs carry the interview invariants today? |

- [x] **A3.** Optional 16th–25th Qs only if thin: e.g. FinBERT-not-in-smoke, confidence-is-trace-only, no neural reranker — do not bloat.  
- [x] **A4.** Cross-check: no answer contradicts ARCHITECTURE §7 / AG1–AG3; no claim that packaging = v1 Done; no fake “LangSmith proven” language.  
- [x] **A5.** Link from INTERVIEW.md to `docs/ARCHITECTURE.md` and `docs/VISION.md` (paths only; keep FAQ self-contained enough for drills).

### Phase B — `GETTING_STARTED.md` (clone-and-run)

**Role split (pinned):** GETTING_STARTED = clone depth; README = skim + link. Avoid duplicating long FAQ content into both files.

- [x] **B1.** Create `alphaguard/GETTING_STARTED.md` at **repo root**.  
- [x] **B2.** Document clean-clone path in order:  
  1. Python via `.python-version` (**3.12**) + `uv sync --all-extras` (or `make sync`)  
  2. `cp -n .env.example .env`  
  3. `ollama pull gemma4:e2b` (fallback: `export OLLAMA_MODEL=qwen3.5:4b` + pull; note 412 → upgrade Ollama)  
  4. `make bundle`  
  5. `make smoke` with **Kafka down** (cite Makefile comment)  
  6. Preflight: `make preflight` / what it checks  
  7. Where envelope is written: `artifacts/runs/*.json` (gitignored)  
  8. macOS `libomp` note (`brew install libomp`; smoke sets `KMP_DUPLICATE_LIB_OK`)  
- [x] **B3.** State defaults: `ALPHAGUARD_RAG_MODE=fixture`; Qdrant/Kafka optional later; smoke does **not** require Compose.  
- [x] **B4.** One-line note: Compose file present ≠ Kafka maturity (point to INTERVIEW theme).  
- [x] **B5.** One-line note: primary model missing → preflight may use fallback (soft warning-debt OK to mention briefly).  
- [x] **B6.** Link back to README + ARCHITECTURE; do not tick VISION boxes from this file.

### Phase C — README diagram + stack table

- [x] **C1.** Add a **simplified** mermaid flowchart derived from ARCHITECTURE §4. Prefer critical path: Replay fixtures → Replay runner → PipelineService → (fixture RetrievalHits / optional Qdrant) → Agent 1 → Agent 2 → Local run summary (+ LS/Phoenix best-effort stubs).  
- [x] **C2.** Diagram honesty: Kafka may appear as optional / later path — do **not** draw Kafka as always-on for smoke. Preserve ARCHITECTURE wording intent: Kafka mandatory in architecture/Compose; **optional for smoke**.  
- [x] **C3.** Add a **stack table** (or clear short table + link to VISION/ARCHITECTURE locked stack): Python/`uv`, LangGraph, Ollama (`gemma4:e2b`), XGBoost gate, fixture RAG default, Compose Kafka+Qdrant (optional for smoke), local envelope mandatory.  
- [x] **C4.** Keep / strengthen: **vertical slice / not v1 complete**; `bundle_kind=fixture` ≠ Option B; LS/Phoenix stubs; Limitations still honest.  
- [x] **C5.** Link `GETTING_STARTED.md` and `INTERVIEW.md` from README Docs section; update Limitations to remove “absent” once artifacts exist (only after files land).  
- [x] **C6.** Trivial AGENTS.md one-liner OK if needed (“guide 02 packaging landed”) — do not reopen stack locks.

### Phase D — Screenshots (`docs/assets/`)

**Capture process (pinned soft default):** **Human runs `make smoke`**; Implement agent follows the **redaction checklist** below and commits curated PNGs only. Tradeoff: slower than pure agent capture, but safer against home-path leaks and invented UI. Agent must **not** fabricate LangSmith/Phoenix UI or invent smoke output.

#### D0 — Human capture (operator)

- [x] **D0a.** With Kafka **down**, run from repo root: `make bundle` (if needed) then `make smoke` (default `gemma4:e2b` or documented fallback). Confirm exit 0.  
- [x] **D0b.** Note the printed envelope path under `artifacts/runs/`.  
- [x] **D0c.** Capture **terminal** screenshot of the successful smoke excerpt (proposal + decision + envelope path hint).  
- [x] **D0d.** Open the envelope JSON; prepare a **curated** view for screenshot (pretty-print selected keys — see D2). Do not git-add `artifacts/`.

#### D1 — Agent redaction checklist (mandatory before commit)

- [x] **D1a.** Create `docs/assets/` if missing.  
- [x] **D1b.** **Redact** any absolute home paths (`/Users/...`, `/home/...`) from visible JSON / terminal crop — especially `obs.local_summary_path`. Prefer relative path text or `artifacts/runs/<id>.json` in captions.  
- [x] **D1c.** Never paste secrets, `.env` contents, or API keys into images or captions.  
- [x] **D1d.** Never edit JSON values to fake `obs.langsmith=ok` / Phoenix success for marketing. Capture honest stub statuses (`skipped` / `failed` / config-driven).  
- [x] **D1e.** Do not invent UI screenshots of LangSmith or Phoenix.

#### D2 — Required assets (≥2)

- [x] **D2a.** `docs/assets/smoke_terminal.png` (name flexible) — terminal smoke excerpt showing success + envelope path hint.  
- [x] **D2b.** `docs/assets/run_envelope_curated.png` (name flexible) — curated envelope JSON showing at least: `status=success`, `rag_mode=fixture`, `resource_mode=replay_fixture`, `obs.langsmith` and `obs.phoenix` stub fields visible.  
- [x] **D2c.** Captions (in README and/or `docs/assets/README.md` short note):  
  - Local run summary is the **mandatory** LLMOps baseline  
  - LangSmith / Phoenix on the envelope are **status stubs** (not real SDK spans)  
  - Agent 1 proposal may vary across runs; **gate policy is deterministic**  
  - Paths redacted for privacy  

- [x] **D3.** Reference both images from README (and optionally GETTING_STARTED).  
- [x] **D4.** Confirm `artifacts/` remains gitignored; only `docs/assets/*` images are committed.

### Phase E — Honesty pass + cross-links

- [x] **E1.** Grep operator docs for accidental “qwen-only DoD,” “LangSmith proven,” “Option B complete,” or “v1 Done” claims; fix if introduced.  
- [x] **E2.** Confirm gemma default + 412/fallback appears in GETTING_STARTED and remains consistent with README / AGENTS / `.env.example`.  
- [x] **E3.** Confirm FAQ + captions state: local envelope fulfills packaging until H2 reversed; packaging-first soft override of ARCHITECTURE §15 cited once (INTERVIEW or GETTING_STARTED “why packaging now” note is enough — do not rewrite ARCHITECTURE in this guide).  
- [x] **E4.** Confirm LICENSE was **not** added as a hard DoD item (optional follow-on only if human expands scope).  
- [x] **E5.** Confirm no Compose `docker compose up` operator appendix was added as a guide-02 requirement.  
- [x] **E6.** Stop. Do not start Kafka E2E, Option B, eval≥20, or Align-docs MV checkbox edits in this guide.

---

## Verification / Definition of Done (this guide)

**Done when all are true:**

1. `INTERVIEW.md` exists at repo root with **≥15** Q&A covering every required theme in Phase A table.  
2. `GETTING_STARTED.md` exists at repo root and documents the clone path in Phase B (Python 3.12, `uv`, gemma/fallback, `make bundle`, `make smoke` Kafka-down, preflight, envelope location, `libomp`).  
3. README contains simplified mermaid (ARCHITECTURE §4 critical path) + stack table; still says vertical slice / not v1 complete; fixture ≠ Option B.  
4. `docs/assets/` contains **≥2** PNGs (terminal smoke + curated envelope) with captions covering LS/Phoenix stubs, path redaction, and Agent 1 variance.  
5. No secrets, no raw `artifacts/` tree, no fabricated LangSmith/Phoenix UI in git.  
6. No product/pipeline code changes required for DoD (doc/link-only diffs).  
7. LICENSE not required; Compose appendix not required.  
8. Operator docs keep `gemma4:e2b` default honesty.  
9. VISION MV packaging boxes are **not** silently checked by this Implement — Align-docs follow-up may tick after Review evidence.

**Explicitly not required for this guide’s DoD:**

- LICENSE file  
- Compose healthcheck / `docker compose up` appendix  
- Kafka producer/consumer E2E  
- Option B train / U4  
- Real LangSmith/Phoenix SDK spans  
- Eval golden growth to ≥20  
- Public GitHub “pinned portfolio” claim  
- Rewriting ARCHITECTURE §15 hard text (soft override citation in packaging docs is enough)  
- Ticking VISION MV checkboxes mid-Implement  

**Suggested verification commands (implementer — after artifacts exist):**

```bash
# From alphaguard/
test -f INTERVIEW.md
test -f GETTING_STARTED.md
test -d docs/assets
find docs/assets -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \) | wc -l   # ≥2
rg -n 'mermaid|GETTING_STARTED|INTERVIEW|docs/assets' README.md
rg -n 'bundle_kind=fixture|LangSmith|Phoenix|gemma4:e2b|vertical slice' README.md GETTING_STARTED.md INTERVIEW.md
# Optional honesty: ensure no absolute home path in committed assets captions/docs
rg -n '/Users/|/home/' docs/assets README.md GETTING_STARTED.md INTERVIEW.md || true
# Do not require make smoke for docs-only Review if screenshots already proven;
# human capture step already ran smoke for assets.
```

Count INTERVIEW Q&A (≥15). Spot-check themes 1–15 against Phase A table.

---

## Blast radius and risks

| Risk | Blast radius | Mitigation in steps |
|------|----------------|---------------------|
| Status theater (fake LS UI / unlabeled stubs) | Portfolio credibility kill | Phase D captions; H2 local-envelope fulfillment; ban fabricated UI |
| Home-path leakage in PNGs | Privacy / scrub | D1 redaction checklist; curated JSON keys |
| Fixture F1=1.0 quoted as quality | ML interview kill | Phase A theme 6; README Limitations |
| Gemma honesty regression | Clone failures; 412 confusion | Phase B + E; mirror README/AGENTS |
| Scope creep to Kafka / SDK / Option B / LICENSE | Calendar burn; Band B drift | Stop conditions; core DoD exclusions |
| Agent 1 variance misread as flaky demo | Reviewer distrust | Captions + FAQ theme 12; do not freeze “golden” proposal |
| GETTING_STARTED ↔ README drift | Support burden | Role split: clone depth vs skim+link |
| Overlong INTERVIEW essay | Unmaintainable; contradicts ARCHITECTURE | Cap 15–25; ARCHITECTURE wins |
| Silent VISION MV checkbox ticks | Status theater | Align-docs owns checkboxes |
| Agents “correct” to Kafka-first (§15) | Wrong next guide | Cite pass-12 soft override in constraints + E3 |
| Committing `artifacts/` or `.env` | Secret/noise leak | gitignore; D4 check |

### Rollback (pass 18 — for Ready check)

Docs + curated assets only. **Rollback** = revert the packaging commit(s); delete `INTERVIEW.md` / `GETTING_STARTED.md` / `docs/assets/*` if needed. No DB/migration/runtime flag to unset. Do not leave VISION MV boxes checked if Align-docs never ran.

---

## Edge-case handling (steps or DoD)

| Edge case | Expected packaging behavior |
|-----------|-----------------------------|
| Old Ollama → `gemma4:e2b` **412** | GETTING_STARTED: upgrade **or** `OLLAMA_MODEL=qwen3.5:4b`; never pretend gemma always works |
| Primary model missing → preflight fallback | Document fallback; soft warning-debt OK |
| Kafka accidentally up during smoke | Docs: smoke does not require Compose; do not imply Kafka was exercised |
| Qdrant down + `RAG_MODE=qdrant` | GETTING_STARTED: default `fixture`; qdrant is optional later |
| Envelope only under gitignored `artifacts/` | Export curated PNGs to `docs/assets/`; never git-add artifacts tree |
| Absolute paths in envelope | Redact before commit (D1) |
| `obs.langsmith=skipped` / `failed` | Caption honesty; do not rewrite JSON for marketing |
| Same event → different Agent 1 `action` | Document as expected; show gate mapping; no golden-proposal chase |
| INTERVIEW contradicts ARCHITECTURE | ARCHITECTURE wins; fix FAQ |
| OOU ticker / `SELL` questions | FAQ → fail-closed + tests |
| macOS `libomp` / XGBoost | Repeat brew note in GETTING_STARTED |
| Clean clone without `make bundle` | Document bundle before smoke |
| Wrong Python | Point at `.python-version` = 3.12 + `uv` |
| Human wants real LangSmith screenshots | Out of scope until H2 reversed + obs guide |
| Diagram shows Kafka always-on | Prefer optional-for-smoke framing |
| Reviewer equates Compose with Kafka DE maturity | INTERVIEW gotcha required |
| FAQ cites fixture F1=1.0 as quality | Ban |

---

## Stop conditions / non-goals

**Stop when** this guide’s DoD is met (docs + assets only).

**Do not:**

- Implement Kafka E2E, Option B train, real LS/Phoenix SDK, neural reranker, brokerage/Lowd  
- Add LICENSE as a hard DoD item (unless human expands scope)  
- Add Compose operator appendix as a guide-02 requirement  
- Silently rewrite VISION MV checkboxes or ARCHITECTURE §15 hard sequencing  
- Re-open guide-01 Implement or AG1–AG3 locks  
- Claim “interview-packaged” / “v1 Done” before Review verifies artifacts  
- Proceed from Write → Ready-check / Implement without human gate  

If a stack or contract change seems required, **stop and ask** — packaging must not reopen VISION/ARCHITECTURE locks.

---

## Open decisions pinned (defaults)

| Decision | Pinned default | Tradeoff | Override |
|----------|----------------|----------|----------|
| Guide 02 = packaging before Kafka/Option B (H1) | **Yes** (pass-12 soft override of ARCHITECTURE §15) | Faster interview ROI; defers DE maturity proof | Human: next interview is Kafka-heavy or U4 chosen |
| H2 accept LS/Phoenix stubs | **Yes** — local envelope fulfills packaging | Honest baseline; no SDK sprawl | Human reverses H2 + obs guide |
| `INTERVIEW.md` / `GETTING_STARTED.md` paths | **Repo root** | Clone-obvious; noisier root | Human: move under `docs/` |
| Screenshot cardinality | **Exactly 2** (terminal + curated envelope) | Enough proof; low maintenance | Human expands set |
| Screenshot capture process | **Human-run `make smoke` + agent redaction checklist** | Safer redaction; slower | Human authorizes agent-only capture with same redaction bar |
| LICENSE in core DoD | **Out** (follow-on polish) | Keeps packaging thin | Human forces MIT/Apache into this guide |
| Compose healthcheck appendix | **Out** | Kafka guide / later | Human expands scope |
| FAQ tone | **Concise staff gotcha FAQ** (2–6 sentence answers) | Drill-friendly; less narrative | Human requests essay tone |
| Public GitHub “pinned” claim | **Do not claim** without human confirm | Avoid status theater | Human confirms visibility/pin |

---

## Refine pass 18 (hub verify)

**Checked vs Refine prompt:** completeness, step order A→E, verification commands, DoD, blast radius, edge cases; plus Ready-check preview dimensions (alignment, rollback).

**Material edits this refine:** Add explicit **Rollback** note (was missing — Ready check asks for rollback clarity). No other DoD holes; pass 17 pins still hold.

**Honest call:** **Ready check next** (not more Refine). Still **not** authorized to Implement.

**Readiness score (Refine preview, /10):** **9.2** — executable packaging guide; residual is Implement craft (FAQ wording, human smoke capture), not design gaps.

---

## Honest readiness (Refine pass 17–18)

- **Write-dev-guide DoD:** met.  
- **Refine-dev-guide:** complete through pass 18 — guide **good to go** for Ready check.  
- **Ready for:** Ready check before code.  
- **Not authorized:** Implement (no INTERVIEW/GETTING_STARTED/assets/LICENSE creation until authorized).  
- **Not claimable:** interview-packaged / v1 complete.  
- **Not the Ready-check stage:** score above is a Refine preview; formal READY/NOT-READY is the next human-gated stage.
