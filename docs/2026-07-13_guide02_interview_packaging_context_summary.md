# Context: Guide 02 — interview packaging

**Date:** 2026-07-13  
**Repos:** `alphaguard` (+ program notes in `second_brain`; no other product repos in-slice)  
**Status:** Ready for dev guide  
**Mode last used:** spoke  
**Stage:** Refine context (pass 15 verify; pass 14 refine); prior Gather = pass 13  
**Handoff:** `second_brain/docs/2026-07-13_alphaguard_refine_context_guide02_pass14_handoff.md` (pass 15 = hub verify; no new spoke handoff)  
**Lens:** Senior AI eng (interview lab ROI) + docs/ops honesty (no status theater) + light ML honesty (`bundle_kind=fixture`)

---

## Problem

AlphaGuard’s **guide-01 replay-first vertical slice is shippable** (pass-9: 20 pytest + `make smoke` exit 0 on `gemma4:e2b`). The product purpose in [`docs/VISION.md`](./VISION.md) is a **late-stage interview lab**, not a private trading system. Interviewers (and Tom’s explain-without-AI drills) still lack the **packaging artifacts** VISION lists as Minimum Viable / Sharing Strategy:

| Expected artifact | Repo reality (re-verified 2026-07-13 pass 14) |
|-------------------|-----------------------------------------------|
| `INTERVIEW.md` (≥15 gotcha Q&A) | **Absent** (root + docs; only this context filename matches `*interview*`) |
| `GETTING_STARTED` clone-and-run path | **Absent** (neither root nor `docs/GETTING_STARTED.md`) |
| README architecture diagram + stack table polish | README is a **stub** Quick Start + Limitations; **no** mermaid/diagram; stack table lives in VISION/ARCHITECTURE only |
| Checked-in screenshots under `docs/assets/` (or similar) | **`docs/assets/` does not exist**; no PNG/JPG/WEBP under `docs/` |
| LICENSE / public polish | **No LICENSE** file at root |
| Gemma default honesty in operator docs | README / AGENTS / `.env.example` already prefer `gemma4:e2b` + 412/fallback notes — packaging must **not** reintroduce “qwen-only DoD” or fake LangSmith screenshots |

Pass-10 called missing packaging a **P1 portfolio gap**. Pass-12 + hub Band B recommend **guide 02 = interview packaging** before Kafka E2E and before Option B (U4-blocked). Guide 01 explicitly deferred INTERVIEW / packaging (`F6`, DoD “not required”).

**One-sentence problem:** The runnable demo exists; the **defendable interview shell** (FAQ, clone path, diagram, honest local-envelope screenshots, gemma default story) does not.

---

## Acceptance criteria

Work item success for **guide 02 (when later implemented)** — criteria refined so Write-dev-guide can pin DoD. This Refine pass does **not** implement them.

- [ ] `INTERVIEW.md` at **repo root** with **≥15** gotcha Q&A covering AG1–AG3, as-of/leakage, gate policy (`BUY` vs `HOLD`/`PASS`), fixture≠Option B, replay-vs-Kafka, RAM/resource modes (`replay_fixture` vs `kafka_integration`), Ollama/`gemma4:e2b` honesty, identity ownership, LS/Phoenix stubs vs local envelope, Agent 1 non-determinism vs deterministic gate
- [ ] `GETTING_STARTED.md` at **repo root** documents clean-clone path: Python via `.python-version` (3.12) + `uv sync --all-extras` → `cp -n .env.example .env` → `ollama pull gemma4:e2b` (fallback `qwen3.5:4b`) → `make bundle` → `make smoke` with **Kafka down**; preflight; where envelope is written; macOS `libomp` note
- [ ] README gains an **architecture diagram** (mermaid acceptable; simplify ARCHITECTURE §4) + **stack table** (or clear link to VISION/ARCHITECTURE) and still says **vertical slice / not v1 complete**; fixture `bundle_kind=fixture` ≠ Option B proof
- [ ] `docs/assets/` contains **≥2 checked-in** screenshots from a successful **local** replay: (1) terminal smoke excerpt, (2) envelope JSON showing `status=success`, `rag_mode=fixture`, `resource_mode=replay_fixture`, `obs.langsmith|phoenix` stubs — **not** fabricated LangSmith UI; captions state LS/Phoenix are stubs; **home paths redacted**
- [ ] Operator docs keep **default `OLLAMA_MODEL=gemma4:e2b`** honesty: needs current Ollama; 412 → upgrade or `qwen3.5:4b`; do not claim gemma without pull/smoke evidence
- [ ] No new pipeline features, no Kafka producer/consumer, no Option B train, no real LangSmith/Phoenix SDK wiring, no LICENSE file required in this guide’s core DoD
- [ ] VISION MV packaging-related boxes become honestly checkable after Implement+Review of guide 02 (Align docs follow-up may tick them) — packaging guide itself must **not** silently rewrite VISION status / MV checkboxes without evidence
- [ ] FAQ / captions reconcile VISION Sharing Strategy “LangSmith (or Phoenix) trace screenshots” wording: **local envelope screenshots satisfy packaging until H2 is reversed**; do not claim real LS/Phoenix spans

**Refine-stage done when:** context accuracy/gaps/edge cases updated, soft unknowns pinned as recommended defaults with tradeoffs, Write-dev-guide readiness re-stated — **met by this file**.

---

## In scope

- Authoring (later) a **thin packaging guide** whose Implement lands docs + screenshots only (plus trivial README/AGENTS cross-links if needed)
- Inventory and constraints for:
  - `INTERVIEW.md` FAQ content themes (from VISION / ARCHITECTURE / pass-9 findings + live envelope behavior)
  - Clone-and-run `GETTING_STARTED.md` derived from README Quick Start + Makefile
  - README diagram (reuse/simplify ARCHITECTURE §4 mermaid) + stack table polish
  - Local-envelope screenshot capture workflow (`make smoke` → `artifacts/runs/*.json` is gitignored — **must copy curated PNGs into `docs/assets/`**)
  - Gemma4 default + fallback honesty (align with README / AGENTS / `.env.example`)
- Restating bans: fixture≠Option B; LS/Phoenix stubs; no Loom; no brokerage / Lowd
- Optional **small** packaging-adjacent notes called out by pass-12 overlooked list **only if guide DoD stays thin**: e.g. one-line preflight-fallback warning mention in GETTING_STARTED; explicit “Compose file ≠ Kafka maturity” in INTERVIEW — **not** full Compose operator proof unless human expands scope

## Out of scope

- Implementation / code changes in this Refine pass
- Full **Write / Refine / Implement** of guide 02 (next stages — Write is next when human says so)
- Live RSS → Kafka E2E; `ingest/producer` / `consumer`; `/trigger`
- Option B `training_events.parquet` / `ml/train` / U4 source selection (hard gate elsewhere)
- Real LangSmith / Phoenix SDK spans (pass-10 **H2** recommend accept stubs; packaging screenshots = **local envelope**)
- Eval growth to ≥20 goldens (pass-12 #2 — parallel follow-on, not this work item’s core)
- Neural reranker / hybrid RRF; FinBERT-in-smoke; brokerage APIs; Lowd Capital
- Re-opening guide-01 Implement or AG1–AG3 locks
- Claiming “v1 Done” or “interview-packaged” before artifacts exist
- Ticking VISION MV boxes for Compose / Option B / 500-event train as part of packaging
- Silent override of ARCHITECTURE §15 sequence text without a later Align-docs note (priority already packaging-first per pass-12; contracts unchanged)
- Adding `LICENSE` as a **hard** guide-02 DoD item (recommended follow-on polish)

---

## Prior art (paths only)

### Product / contracts / agent rails

- `alphaguard/docs/VISION.md` — interview lab purpose; Sharing Strategy; MV boxes for INTERVIEW / polish / screenshots; gemma default lock
- `alphaguard/docs/ARCHITECTURE.md` — §4 mermaid; §13 obs + screenshot debt; §15 build sequencing (soft conflict with packaging-first priority); §16 resource modes
- `alphaguard/README.md` — Quick Start stub; Limitations already admit missing packaging
- `alphaguard/AGENTS.md` — vertical slice; gemma/fallback; AG1–AG3 one-liners
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md` — shipped slice; F6 deferred INTERVIEW; DoD excludes packaging
- `alphaguard/.env.example` — `OLLAMA_MODEL=gemma4:e2b`, `OLLAMA_FALLBACK_MODEL=qwen3.5:4b`, LS/Phoenix flags
- `alphaguard/Makefile` — `smoke` / `preflight` / `bundle` / `sync` / `test` targets (Kafka must stay down for smoke)
- `alphaguard/.python-version` — `3.12` (clone path should mention)
- `alphaguard/docker-compose.yml` — Kafka + Qdrant present; **not** smoke requirement

### Program / prior Workflow OS passes

- `second_brain/docs/2026-07-13_alphaguard_prioritize_next_work_pass12.md` — **TOP = packaging guide 02**
- `second_brain/docs/2026-07-13_prioritize_next_work_pass12_fan_in.md` — hub Band B: AlphaGuard packaging
- `second_brain/docs/2026-07-13_alphaguard_review_impl_pass9.md` — shippable slice; gemma smoke evidence; R3–R5 residuals
- `second_brain/docs/2026-07-13_alphaguard_align_docs_pass10.md` — packaging P1 debt; H1/H2/U4; no INTERVIEW/GETTING_STARTED/assets
- `second_brain/docs/2026-07-12_portfolio_vision_workspace_and_decisions.md` — AG1–AG3 program locks (referenced by VISION/ARCHITECTURE)
- `second_brain/docs/2026-07-13_alphaguard_gather_context_guide02_pass13_handoff.md` — Gather spoke brief
- `second_brain/docs/2026-07-13_alphaguard_refine_context_guide02_pass14_handoff.md` — this Refine spoke brief
- `second_brain/docs/2026-07-13_refine_context_guide02_pass14_shared_handoff.md` — shared Refine rules

### Runnable evidence (for future screenshots / FAQ claims)

- `alphaguard/data/fixtures/` — `replay_events.jsonl` (7), `retrieval_hits.json`, `feature_rows.json`, `model_bundle_fixture/` (`bundle_kind=fixture`; `metrics.train_f1_at_threshold=1.0` on synthetic `n_rows=64`)
- `alphaguard/artifacts/runs/*.json` — local envelopes (**gitignored** via `.gitignore` `artifacts/`); live keys include `status`, `proposal`, `decision`, `obs.langsmith|phoenix`, `rag_mode=fixture`, `resource_mode=replay_fixture`, `mode=replay`
- `alphaguard/eval/golden_cases.jsonl` — 7 stubs (eval debt; FAQ may cite “unit tests carry invariants”)
- `alphaguard/tests/test_gate.py` — deterministic gate examples (`HOLD`/`PASS` approve; `BUY` reject when score ≥ threshold)
- `alphaguard/docs/ARCHITECTURE.md` §4 flowchart — candidate source for README diagram

### Packaging inventory (filesystem — Gather + Refine re-check)

| Path / pattern | Status | Verification |
|----------------|--------|--------------|
| `INTERVIEW.md` | **Missing** | `test -f` → no (root); find depth≤3 → none (except this context doc) |
| `GETTING_STARTED.md` / `docs/GETTING_STARTED.md` | **Missing** | same |
| `docs/assets/` | **Missing** | `ls docs/assets` → No such file |
| Screenshots (`*.png|jpg|webp` under `docs/`) | **Missing** | `find docs` → empty |
| README mermaid / architecture diagram | **Missing** | `rg mermaid README.md` → no hits |
| README stack table | **Missing** (table is in VISION) | README = Quick Start + Docs links + Limitations |
| `LICENSE` | **Missing** | no `LICENSE*` at root |
| Local envelope capability | **Present** (runtime) | 4 files under `artifacts/runs/`; not for git |
| Gemma default docs | **Present** | README, AGENTS, `.env.example` |
| Remote | Present | `origin` = `https://github.com/Alpha-W0lf/alphaguard.git` (public-pin claim still soft / not required for local docs) |

---

## Risks and blast radius

| Risk | Why it matters | Blast radius | Mitigation for guide 02 |
|------|----------------|--------------|-------------------------|
| **Status theater in screenshots** | Fake LangSmith UI or unlabeled stub `obs.langsmith=ok` misleads interviewers | Portfolio credibility; pass-10 P1 repeat | Screenshots = terminal smoke + envelope JSON; captions: local baseline; LS/Phoenix stubs |
| **VISION “LangSmith screenshots” wording** | Sharing Strategy literally says LS/Phoenix screenshots | Agents/humans may invent fake UI to “match VISION” | Pin: local envelope **fulfills packaging intent** until H2 reversed; Align-docs may soften VISION row later |
| **Fixture metrics quoted as Option B** | `manifest.metrics.train_f1_at_threshold=1.0` on synthetic 64 rows looks “too good” | ML interview kill | INTERVIEW + README ban: `bundle_kind=fixture` only |
| **Gemma honesty regression** | Docs say gemma default but guide implies qwen-only, or claim gemma without Ollama version caveat | Clone-and-run failures; 412 on old Ollama | Mirror README: default `gemma4:e2b`; upgrade or fallback |
| **Scope creep into Kafka / SDK / Option B / LICENSE** | Burns 6–7 day budget; U4 blocks train | Calendar; hub Band B drift | Guide stop conditions = docs+assets only; LICENSE follow-on |
| **Committing secrets / full `.env` / raw artifacts tree** | Key leak; noisy git | Security; PR size | Screenshots curated; never commit `.env`; `artifacts/` stays gitignored |
| **Home-path leakage in envelope PNGs** | Live envelopes embed absolute `obs.local_summary_path` under `/Users/tom/...` | Privacy | Redact/crop paths before commit; prefer pretty-print of selected keys |
| **Agent 1 non-determinism in screenshots** | Same `evt-aapl-001` yields `BUY`+reject or `HOLD`+approve across runs | Reviewer confusion; “flaky demo” narrative | Caption: proposal is LLM-sampled; gate policy is deterministic; FAQ covers both |
| **Ticking VISION MV boxes mid-packaging** | Compose / Option B / 500-event remain unchecked | Status theater | Packaging Implement may only enable honest checks for diagram/INTERVIEW/screenshots polish — Align-docs owns checkbox updates |
| **ARCHITECTURE §15 vs packaging-first** | Fresh agents may start Kafka guide instead | Hub ordering | Context + future Align note; pass-12 soft override already recorded |
| **GETTING_STARTED duplicates README then drifts** | Two operator paths diverge | Support burden | GETTING_STARTED = clone depth; README = skim + link |
| **Overlong INTERVIEW.md** | Becomes unmaintainable essay | Reviewer fatigue | Cap ~15–25 Qs; point to ARCHITECTURE for contracts |
| **LICENSE deferred forever** | Blocks “public portfolio” claim | Sharing strategy | Soft follow-on; not core DoD |

---

## Edge cases

| Edge case | Expected packaging behavior |
|-----------|-----------------------------|
| Reviewer has old Ollama → `gemma4:e2b` **412** | GETTING_STARTED: upgrade Ollama **or** `export OLLAMA_MODEL=qwen3.5:4b` + pull; do not pretend gemma always works |
| Primary model missing → preflight silent fallback (pass-9 R4) | Document fallback; optional note that warning log may still be soft debt |
| Kafka accidentally up during smoke | Still OK for fixture RAG, but docs must say smoke **does not require** Compose; do not imply Kafka was exercised |
| Qdrant down + someone flips `ALPHAGUARD_RAG_MODE=qdrant` | GETTING_STARTED: default `fixture`; qdrant is optional later path |
| Envelope under `artifacts/runs/` not in git | Screenshots must be **exported** to `docs/assets/`; do not “fix-add artifacts/” |
| Envelope contains absolute home paths | Redact `obs.local_summary_path` (and any other absolute paths) in PNGs / captions |
| `obs.langsmith=skipped` / `failed` on real runs | Caption honesty; never edit JSON to fake `ok` for marketing |
| Same smoke event → different Agent 1 `action` across runs | Document as expected LLM variance; show gate mapping; do not chase a “golden” proposal screenshot |
| INTERVIEW answers contradict ARCHITECTURE | ARCHITECTURE wins; FAQ paraphrases, does not soften AG1–AG3 |
| Out-of-universe ticker / `SELL` questions | FAQ points to fail-closed behavior + tests |
| macOS `libomp` / XGBoost | Already in `.env.example` comment; GETTING_STARTED should repeat brew note |
| Clean clone without `make bundle` | Smoke needs fixture bundle path — document `make bundle` before smoke |
| Clean clone wrong Python | Point at `.python-version` = 3.12 and `uv` (`make sync` / `uv sync --all-extras`) |
| Human wants LangSmith screenshots “for portfolio” | Out of scope until H2 reversed + obs guide; packaging uses local envelope only |
| Diagram shows Kafka as always-on critical path | Prefer ARCHITECTURE wording: Kafka mandatory in architecture/Compose; **optional for smoke** / `replay_fixture` |
| Reviewer equates Compose file with Kafka DE maturity | INTERVIEW gotcha: Compose present ≠ producer/consumer/delivery contract proven |
| FAQ cites fixture F1=1.0 as model quality | Ban; cite `bundle_kind=fixture` + synthetic rows |

---

## Unknowns (must resolve or escalate)

| Unknown | Recommended default (pinned for Write-dev-guide) | Tradeoff | Blocking? |
|---------|--------------------------------------------------|----------|-----------|
| Exact path for GETTING_STARTED | **`./GETTING_STARTED.md` (repo root)** | Root matches VISION naming next to `INTERVIEW.md` and is clone-obvious; `docs/` keeps root cleaner but hides the operator path | **No** — default pinned |
| INTERVIEW.md location | **Repo root `INTERVIEW.md`** | Matches VISION literal name; slightly noisier root | **No** — default pinned |
| Screenshot set cardinality / subjects | **Exactly 2:** (1) terminal smoke excerpt showing success + envelope path hint; (2) curated envelope JSON with `status`, `rag_mode`, `resource_mode`, `obs` stubs visible | More images = more maintenance; terminal-only under-proves local LLMOps claim | **No** — default pinned |
| LICENSE in guide-02 DoD? | **Out of core DoD** (follow-on polish) | AI KB packaging may include LICENSE; AlphaGuard interview ROI is FAQ/clone/diagram/screenshots first | **No** — default pinned |
| Thin Compose `docker compose up` appendix in guide 02? | **Out** (belongs Kafka guide / optional later appendix) | Keeps packaging thin; leaves Compose≠maturity FAQ as prose only | **No** — default pinned |
| H1 packaging-before-Kafka/Option B | Treat as **yes** for Write-dev-guide (handoff-scoped) | Override only if next interview is Kafka-heavy or U4 chosen | Soft — not blocking Write |
| H2 accept LS/Phoenix stubs | Treat as **yes** | Packaging does not sprawl into SDK | Soft — not blocking Write |
| Screenshot capture process | Prefer **human-run `make smoke` + agent-assisted capture/redaction checklist**; agent must not invent UI | Human capture is slower but safer for path redaction; pure agent capture risks leaking home paths | Soft process — detail in Write-dev-guide |
| Public GitHub pin / visibility | Soft; remote exists (`Alpha-W0lf/alphaguard`). Do **not** claim “pinned public portfolio” in packaging docs without human confirm | Local packaging does not need pin | Soft |
| Exact ≥15 FAQ question list | Draft in Write-dev-guide from AG1–AG3 + ARCHITECTURE failure modes + pass-9 R3–R5 + non-determinism/gate + Compose≠maturity | Human may edit tone | No |

---

## Recommended approach

1. **Write-dev-guide next** for guide 02 only — thin, ordered checklist: FAQ → GETTING_STARTED → README diagram/stack → `docs/assets` screenshots → honesty pass (gemma, fixture, stubs, path redaction, non-determinism) → stop.  
2. **Reuse**, don’t reinvent: ARCHITECTURE §4 mermaid (simplified for README); README Quick Start as the seed for GETTING_STARTED; VISION Sharing Strategy as the artifact checklist; live envelopes as the screenshot source of truth.  
3. **Screenshot doctrine:** prove **mandatory local run summary**; explicitly label remote tracers as not yet real; redact absolute paths.  
4. **No code path changes** unless a one-line doc/link fix is required for accuracy; no Kafka, no train, no SDK, no LICENSE-as-DoD.  
5. **After Implement+Review:** separate Align-docs pass may check VISION packaging-related polish boxes and note ARCHITECTURE §15 packaging-before-Kafka priority (soft conflict already known).  
6. **Parallel (not this guide):** eval ≥20 remains pass-12 #2; do not block packaging on it.

**Triviality check:** Not trivially small — multiple artifacts + honesty constraints + screenshot process. **Do not skip Write-dev-guide.**

---

## Open decisions (human) — defaults pinned; override only if needed

1. **Confirm guide 02 = packaging first** (closes pass-10 H1) — **default yes** (already handoff-scoped). Override only if next interview is Kafka-heavy or U4 already chosen.  
2. **H2:** Accept LS/Phoenix stubs for packaging screenshots? — **default yes**.  
3. **Paths:** **`INTERVIEW.md` + `GETTING_STARTED.md` at repo root** (pinned). Override to `docs/` only if you want a docs-only tree.  
4. **LICENSE in guide 02?** — **default no** (follow-on). Say yes only to force MIT/Apache stub into the same guide.  
5. **Compose healthcheck appendix in guide 02?** — **default no**.  
6. **Screenshot capture:** human-run smoke + paste/redact assets vs agent-assisted `screencapture` — **default human smoke + agent redaction checklist** (paths must not leak).

---

## Evidence opened this pass (Gather — pass 13)

### Rails / stage / template / handoff

- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md` (full)
- `second_brain/docs/workflow_os/rails/ALWAYS.md`
- `second_brain/docs/workflow_os/rails/LEARNING_MODE.md`
- `second_brain/docs/workflow_os/stages/gather-context.md`
- `second_brain/docs/workflow_os/templates/context-summary.md`
- `second_brain/docs/2026-07-13_alphaguard_gather_context_guide02_pass13_handoff.md`

### Repo truth

- `alphaguard/docs/VISION.md`
- `alphaguard/docs/ARCHITECTURE.md`
- `alphaguard/README.md`
- `alphaguard/AGENTS.md`
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md`
- `alphaguard/.env.example`
- `alphaguard/Makefile`
- `alphaguard/.gitignore`
- `alphaguard/data/fixtures/model_bundle_fixture/manifest.json`

### Prior passes

- `second_brain/docs/2026-07-13_alphaguard_prioritize_next_work_pass12.md`
- `second_brain/docs/2026-07-13_prioritize_next_work_pass12_fan_in.md`
- `second_brain/docs/2026-07-13_alphaguard_review_impl_pass9.md` (through ranked findings)
- `second_brain/docs/2026-07-13_alphaguard_align_docs_pass10.md`

### Commands / filesystem checks (Gather 2026-07-13)

```bash
# From alphaguard/
ls -la docs/                          # VISION, ARCHITECTURE, brainstorm, dev_guides/ — no assets/
ls docs/assets                        # No such file or directory
test -f INTERVIEW.md                  # INTERVIEW=no
test -f GETTING_STARTED.md            # GETTING_STARTED=no
find docs -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \)
                                      # empty
find . -maxdepth 3 \( -iname '*interview*' -o -iname '*getting*started*' -o -iname '*screenshot*' \)
                                      # empty (no packaging filenames)
wc -l eval/golden_cases.jsonl         # 7
wc -l data/fixtures/replay_events.jsonl  # 7
ls artifacts/runs/                    # local envelopes present (gitignored)
# Sample envelope ee76b888-… : status=success, rag_mode=fixture,
#   obs={langsmith: skipped, phoenix: skipped}
ls LICENSE*                           # none
rg -n 'mermaid|INTERVIEW|GETTING_STARTED|screenshot' README.md
                                      # Limitations mention absences; no diagram
```

**Not re-run Gather:** `make smoke` / full pytest (trust pass-9 evidence; packaging Gather does not need green-CI re-proof).

---

## Evidence opened this refine pass (pass 14)

### Rails / stage / template / handoffs

- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`
- `second_brain/docs/workflow_os/rails/ALWAYS.md`
- `second_brain/docs/workflow_os/rails/LEARNING_MODE.md`
- `second_brain/docs/workflow_os/stages/refine-context.md`
- `second_brain/docs/workflow_os/templates/context-summary.md`
- `second_brain/docs/2026-07-13_refine_context_guide02_pass14_shared_handoff.md`
- `second_brain/docs/2026-07-13_alphaguard_refine_context_guide02_pass14_handoff.md`
- `second_brain/docs/2026-07-13_refine_context_guide02_pass14_program_note.md`

### Repo re-verification (live)

- Re-read: this context file; `README.md`; `AGENTS.md`; `Makefile`; `.env.example`; `.gitignore`; `.python-version`; `docker-compose.yml`; `data/fixtures/model_bundle_fixture/manifest.json`
- Skimmed: `docs/VISION.md` (MV + Sharing Strategy); `docs/ARCHITECTURE.md` §4/§15/§16; guide 01 DoD/`F6`; pass-12 packaging TOP + overlooked list
- Parsed all 4 local envelopes under `artifacts/runs/`:
  - keys: `status`, `proposal`, `decision`, `obs`, `rag_mode`, `resource_mode`, `mode`, …
  - `status=success`, `rag_mode=fixture`, `resource_mode=replay_fixture`, `obs.langsmith=skipped`, `obs.phoenix=skipped`
  - **path leak:** `obs.local_summary_path` includes `/Users/tom/...`
  - **non-determinism:** same `evt-aapl-001` → `BUY`+reject **or** `HOLD`+approve across runs

### Commands (Refine 2026-07-13)

```bash
# From alphaguard/
test -f INTERVIEW.md; test -f GETTING_STARTED.md; test -f docs/GETTING_STARTED.md
# → all missing
ls docs/assets                        # No such file
find docs -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \)  # empty
ls LICENSE*                           # none
find . -maxdepth 3 \( -iname '*interview*' -o -iname '*getting*started*' -o -iname 'LICENSE*' \)
# → only this context summary filename
rg -n 'mermaid|INTERVIEW|GETTING_STARTED|screenshot|assets' README.md
# → Limitations admit absences; no diagram
cat Makefile                          # smoke forces replay+fixture; Kafka comment present
wc -l eval/golden_cases.jsonl data/fixtures/replay_events.jsonl  # 7 / 7
python3 -c '…inspect artifacts/runs/*.json…'  # path leak + BUY/HOLD variance confirmed
git remote -v                         # origin Alpha-W0lf/alphaguard.git
```

**Still not re-run:** `make smoke` / full pytest (packaging Refine does not need CI re-proof; screenshot Implement will re-smoke).

---

## Evidence opened this refine pass (pass 15 — verify)

**Purpose:** Second human-gated Refine pass. Re-check accuracy / gaps / stale claims; no Write-dev-guide / Implement.

**Live re-verify (2026-07-13 evening):**

```bash
test -f INTERVIEW.md; test -f GETTING_STARTED.md; test -f LICENSE; ls docs/assets
# → all missing (same as pass 14)
```

**Material content changes this pass:** **None.** Pass 14 inventory, soft pins, path-leak/variance doctrine, and in/out scope remain accurate. Updating readiness only to record verify.

---

## Learning notes (new this refine pass)

1. **Deterministic gate vs stochastic proposer** — Agent 1’s `BUY|HOLD|PASS` is LLM-sampled; Agent 2’s policy map is fixed. Live envelopes prove the same event can show different proposals while the gate still applies the same rules (`BUY` + high downside → reject; `HOLD`/`PASS` → approve). Packaging that freezes one proposal screenshot without explaining variance teaches the wrong mental model.  
2. **Evidence that contains PII-shaped paths** — A “true” local envelope is still unsafe to screenshot raw if it embeds absolute home directories. Portfolio artifacts need a **redaction step**, not only a “don’t fake LangSmith” rule.  
3. **Architecture sequence ≠ interview value order** — ARCHITECTURE §15 lists packaging after Kafka/Option B as a dependency sketch. Pass-12 soft-overrides that for ROI because packaging needs only the green vertical slice. Write-dev-guide must cite the override explicitly so agents do not “correct” back to Kafka-first mid-guide.

---

## Honest readiness

- **Ready for Write dev guide?** **Yes** — pass 14 pins hold; pass 15 live re-verify found **no material gaps or stale claims**. Soft residuals stay for Write-dev-guide (FAQ tone, H1 ceremony, LICENSE follow-on, Compose appendix).  
- **Still weak (non-blocking):** exact FAQ wording/tone; human confirmation phrase for H1 if desired for ceremony; public “pinned” GitHub claim; LICENSE follow-on; optional Compose appendix still deferred.  
- **Not ready for Implement** until Write (+ optional Refine) + Ready-check per Workflow OS.  
- **Not ready to claim interview-packaged / v1 Done** until guide 02 Implement+Review lands artifacts.  
- **Pass 15:** Stopped for human — no silent multi-pass; no Write/Implement.

### QUALITY_STANDARD §5 (this Refine)

- [x] Assumptions listed or replaced with evidence / pinned defaults + tradeoffs  
- [x] Did not rush; did not invent INTERVIEW content or screenshots  
- [x] Mode/Stage/artifacts declared (spoke Refine; this file)  
- [x] Edge cases + blast radius strengthened (path leak, non-determinism, VISION LS wording, MV checkbox theater)  
- [x] Findings written to dated context + handoff Results  
- [x] Spoke stayed in AlphaGuard packaging slice; **no Write-dev-guide; no Implement**  
- [x] Verification = paths/commands above; honest Write-dev-guide readiness  
