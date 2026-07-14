# Dev Guide 03 — Eval harness ≥20 goldens

**Date:** 2026-07-14  
**Repo:** `alphaguard`  
**Work item:** Guide 03 — eval harness ≥20 goldens (executable, anti-theater)  
**Stage that authored this:** Write-dev-guide (pass 28)  
**Status:** Draft — awaiting Ready check

**Context SSOT:** `alphaguard/docs/2026-07-14_guide03_eval_harness_context_summary.md`  
**Prerequisite:** Guide 01 vertical slice shippable; Guide 02 interview packaging shippable (pass-24). This guide grows **eval goldens + thin harness** only — no Kafka, no Option B, no packaging redo.

---

## Objective

Grow the interview eval surface from a **7-stub count theater** to an **executable ≥20 golden harness**:

1. `eval/golden_cases.jsonl` — **≥20** distinct `case_id`s covering schema, identity overwrite, as-of/future-hit rejection, gate determinism, `SELL` reject, and OOU reject (theme allocation **5 / 3 / 4 / 6 / 2**).  
2. Thin package loader under `src/alphaguard/eval/` — fail-closed on missing universal keys / duplicate ids; per-`check` payload keys from the frozen field skeleton.  
3. **Pytest parametrize** executes each golden against real public façades (`Agent1Proposal` / `NewsEvent` / `RetrievalHit`, `stamp_identity`, `filter_hits_as_of`, `apply_policy`) — a golden without an executor does **not** count.  
4. Raise presence/coverage floor from `>= 5` to **`>= 20`** + theme inventory asserts.  
5. Honesty docs — README Limitations + INTERVIEW §15 match new count; still **not** live-Ollama numeric schema-pass rates / not Option B metrics.

**Success signal:** `uv run pytest` green with ≥20 parametrized goldens executing; reviewer can open JSONL + INTERVIEW and see honest “suite + goldens” without Kafka, Option B train, or LLM rate theater.

---

## Learning notes (new for this guide)

1. **Golden vs unit test** — A **unit test** hard-codes one scenario in Python. A **golden** is a data row (JSONL) that the same thin runner executes. Goldens are the interview-facing inventory (“here are 20 contracts we re-run”); unit tests stay for deep edges. Overlap is OK; do not delete `test_gate` / `test_asof` / `test_contracts` in this guide.

2. **Anti-theater / executable harness** — Counting lines in JSONL without running them is **count theater**. The harness is the small loader + `check` → façade map + pytest parametrize. If a row cannot execute, it does not satisfy DoD.

3. **Allocation recipe vs full inventory** — Pass 27 pinned **theme quotas** (how many of each `check`), not every `case_id` string. This guide freezes illustrative ids + the recipe as locked defaults; Implement may rename within a theme if counts/minima hold.

4. **Field skeleton as fail-closed design** — Universal keys (`case_id`, `check`, `expect`) plus per-`check` payload keys turn expect-only stubs into an explicit defect. Enrich sparse stubs in the **same** Implement PR as growth.

5. **Structural schema checks ≠ live-Ollama rates** — ARCHITECTURE §12 “schema pass rate” in this guide means **ok/reject counts on goldens**, never a CI percentage against a live LLM. Numeric LLM rates stay deferred (VISION Future / separate work).

---

## References (paths only)

### Product / contracts / rails

- `alphaguard/docs/VISION.md`
- `alphaguard/docs/ARCHITECTURE.md` (§5 eval stub; §7.4 gate; §8 as-of; §10 failure modes; §11 fixtures; §12 testing/eval; §13 obs; §15 sequence)
- `alphaguard/AGENTS.md`
- `alphaguard/README.md`
- `alphaguard/INTERVIEW.md` (§15 unit tests vs golden stubs)
- `alphaguard/GETTING_STARTED.md`
- `alphaguard/docs/dev_guides/2026-07-12_dev_guide_01_replay_first_vertical_slice.md`
- `alphaguard/docs/dev_guides/2026-07-13_dev_guide_02_interview_packaging.md`
- `alphaguard/docs/2026-07-14_guide03_eval_harness_context_summary.md`

### Eval / code under test

- `alphaguard/eval/golden_cases.jsonl`
- `alphaguard/src/alphaguard/eval/__init__.py`
- `alphaguard/tests/test_eval_stubs.py`
- `alphaguard/tests/test_contracts.py`
- `alphaguard/tests/test_gate.py`
- `alphaguard/tests/test_asof.py`
- `alphaguard/tests/test_fixtures.py`
- `alphaguard/src/alphaguard/ml/gate.py`
- `alphaguard/src/alphaguard/pipeline/service.py`
- `alphaguard/src/alphaguard/rag/asof.py`
- `alphaguard/data/fixtures/model_bundle_fixture/manifest.json`
- `alphaguard/data/fixtures/replay_events.jsonl`

### Program / pins

- `second_brain/docs/2026-07-13_alphaguard_prioritize_next_work_pass12.md`
- `second_brain/docs/2026-07-14_alphaguard_refine_context_guide03_pass27.md`
- `second_brain/docs/2026-07-14_write_dev_guide_guide03_pass28_shared_handoff.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **Eval growth + thin harness only.** No Kafka producer/consumer / `/trigger` / Compose maturity. No Option B `ml/train` / U4 / `training_events.parquet`. No packaging redo (`INTERVIEW` FAQ rewrite beyond §15 honesty, no new `docs/assets/`). No Align-docs VISION / ARCHITECTURE §13 status ticks in core DoD.  
2. **AG1–AG3 locked** — goldens exercise contracts; do not soften them. ARCHITECTURE wins on wording conflicts.  
3. **Anti-theater:** every golden row must be executable via pytest parametrize against real façades. JSONL-only growth without a runner **fails DoD**.  
4. **Loader home:** `load_golden_cases` (and optional thin dispatch helpers) live under **`src/alphaguard/eval/`**; tests import the package — do not leave the only loader test-local forever.  
5. **Check dispatch map (frozen):**  
   - `schema` → `Agent1Proposal` / `NewsEvent` / `RetrievalHit` validation  
   - `identity` → `PipelineService.stamp_identity`  
   - `asof` → `filter_hits_as_of`  
   - `gate` → `DownsideRiskGate.apply_policy` (prefer `force_score`; no live LLM; avoid XGBoost load per case when policy-only)  
   - `oou` → `NewsEvent` validator and/or fixture fail-closed  
6. **Do not** route goldens through full `PipelineService` orchestration / Kafka / live Ollama for numeric rates.  
7. **Fixture ≠ Option B:** never assert fixture `metrics.train_f1_at_threshold=1.0` as model quality; `bundle_kind=fixture` is plumbing only.  
8. **Threshold honesty:** read live `gate.manifest.score_threshold` (float noise ≈ `0.45000000000000007`); **never hardcode `0.45`** in asserts or boundary `force_score` construction.  
9. **Vol veto:** committed fixture has `vol_veto_enabled=false`. Vol-veto goldens are **optional** (not core DoD); if included, use a **tmp manifest** only — do not flip the committed fixture.  
10. **Replay fixture headline growth to ≥20** (`data/fixtures/replay_events.jsonl`) is **out** (ARCHITECTURE §11 soft debt) unless human expands.  
11. **Keep existing unit tests**; goldens are additive data-driven coverage. Prefer ≤300 lines/file (hard max 400) for new eval modules.  
12. Still say **vertical slice / not v1 complete / not eval-complete / not portfolio-ready**.  
13. **Pass-12 lock:** guide 03 = eval ≥20 (not Kafka-first despite ARCHITECTURE §15 soft conflict). Cite override; do not rewrite §15 hard text in this guide.

---

## Soft pins (locked defaults — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Theme allocation | **schema 5 / identity 3 / asof 4 / gate 6 / oou 2 = 20**; soft minima 3/2/3/4/2; extras only on these themes |
| JSONL universal keys | Every row: `case_id` (unique), `check`, `expect` |
| JSONL field skeleton | Per-`check` keys in Phase A table (freeze; enrich sparse stubs) |
| Harness shape | JSONL ≥20 + **pytest parametrize** executing each `check` |
| Loader location | **`src/alphaguard/eval/`** |
| Floor assert | Raise `>= 5` → **`>= 20`** + theme coverage |
| Gate path | `apply_policy(action, force_score, vol)` preferred |
| Schema-pass wording | Structural golden ok/reject counts — **not** live-Ollama numeric rates |
| Hard bans | No Kafka; no Option B; no live-Ollama numeric schema-pass % in DoD |

### Soft-default theme allocation (total = 20)

| Theme (`check`) | Count | Soft minimum | Intent |
|-----------------|------:|-------------:|--------|
| `schema` | **5** | 3 | valid BUY; reject SELL; HOLD ok; PASS ok; one bad-field (confidence OOB **or** confidence string **or** empty rationale) |
| `identity` | **3** | 2 | ticker overwrite; `event_id` overwrite; both mismatch stamped from input |
| `asof` | **4** | 3 | future drop; `available_at == published_at` keep; past-only keep; empty-after-filter |
| `gate` | **6** | 4 | BUY high→reject; HOLD→approve; PASS→approve; BUY below threshold→approve; BUY `== score_threshold`→reject; determinism twin |
| `oou` | **2** | 2 | TSLA (or equiv) reject; second OOU symbol **or** fixture-load fail-closed |
| **Total** | **20** | — | `SELL` reject lives under `schema` (`schema_reject_sell`); no parallel unsupported-action theme |

### Soft-default JSONL field skeleton

**Universal (every row):** `case_id`, `check`, `expect`. Loader **fail-closed** if any missing or `case_id` duplicates.

| `check` | Required payload keys | Optional / notes | Façade |
|---------|----------------------|------------------|--------|
| `schema` | `action`, `confidence` | May include `rationale`, `event_id`, `ticker`, or hit-shaped fields for bad-field cases | `Agent1Proposal` / `NewsEvent` / `RetrievalHit` |
| `identity` | `llm_ticker`, `input_ticker`, `llm_event_id`, `input_event_id` | Enrich existing stub (today tickers only) | `PipelineService.stamp_identity` |
| `asof` | `published_at` (aware UTC ISO), `hits` (array) | Each hit: `document_id`, `text`, `ticker`, `available_at`, `source` | `filter_hits_as_of` |
| `gate` | `action`, `force_score` | Optional `volatility_20d` (default low e.g. `0.1`); boundary cases derive `force_score` from **live** manifest | `DownsideRiskGate.apply_policy` |
| `oou` | `ticker` | Optional `via: "news_event" \| "fixture"` for second case | `NewsEvent` / fixture loader |

---

## Acceptance criteria (Implement must meet)

Copied/refined from context SSOT — do not invent extra scope:

- [ ] `eval/golden_cases.jsonl` contains **≥20** distinct `case_id`s (evidence: `wc -l` / JSON parse ≥20; unique ids)  
- [ ] Cases cover themes: **schema**, **identity** overwrite, **as-of** / future-hit rejection, **gate** determinism (BUY reject vs HOLD/PASS approve), **SELL** reject, **OOU** ticker reject — allocation **5/3/4/6/2** (or ≥ soft minima with sum ≥20)  
- [ ] Goldens are **not** count-only theater: pytest parametrize executes each case against real façades  
- [ ] `load_golden_cases` (or equivalent) lives under **`src/alphaguard/eval/`**; tests import it  
- [ ] Presence/coverage assert raises floor from `>= 5` to **`>= 20`** and asserts theme coverage / required checks present  
- [ ] Sparse stubs enriched (`asof_drop_future` payloads; `identity_overwrite` gains event_id pair)  
- [ ] Documented **deferred**: live-Ollama numeric LLM schema-pass rate; Agent 1 hold-out on 50 headlines; Option B metrics; fixture-bundle F1 never quoted as model quality  
- [ ] No Kafka; no Option B / U4 / `ml/train`; no packaging redo; no Align-docs VISION checkbox edits in core DoD  
- [ ] README Limitations + INTERVIEW §15 updated to match new count/honesty  
- [ ] Existing unit tests remain green; smoke path unchanged (Kafka still not required)  

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — Freeze JSONL contract + enrich plan

- [ ] **A1.** Confirm `eval/golden_cases.jsonl` baseline is still **7** unique rows before edits (`wc -l` + parse).  
- [ ] **A2.** Freeze universal keys + per-`check` skeleton from Soft pins (do not reopen). Document fail-closed load errors: missing key, duplicate `case_id`, unknown `check`.  
- [ ] **A3.** Plan enrichment for existing sparse rows:  
  - `asof_drop_future` — add `published_at` + `hits` (at least one future hit)  
  - `identity_overwrite` — add `llm_event_id` + `input_event_id` (expect stamped ticker + event_id from input)  
- [ ] **A4.** Confirm gate boundary cases will read **live** `score_threshold` from fixture manifest at test time (no hardcoded `0.45`).  
- [ ] **A5.** Confirm vol-veto cases are **optional / out of core DoD** unless Implement adds tmp-manifest only.

### Phase B — Author ≥20 goldens (allocation recipe)

**Illustrative `case_id` inventory (Implement may rename within theme if counts hold):**

| `case_id` | `check` | `expect` (illustrative) | Notes |
|-----------|---------|-------------------------|-------|
| `schema_valid_buy` | schema | ok | keep / enrich if needed |
| `schema_reject_sell` | schema | reject | keep (`SELL`) |
| `schema_hold_ok` | schema | ok | **new** |
| `schema_pass_ok` | schema | ok | **new** |
| `schema_bad_confidence` | schema | reject | **new** — pick one: OOB confidence, string confidence, or empty rationale |
| `identity_overwrite` | identity | stamped input ticker (+ event_id) | **enrich** event_id pair |
| `identity_event_id_overwrite` | identity | stamped input event_id | **new** |
| `identity_both_mismatch` | identity | both stamped from input | **new** |
| `asof_drop_future` | asof | future_hit_dropped | **enrich** payloads |
| `asof_equal_boundary_keep` | asof | kept | **new** — `available_at == published_at` |
| `asof_past_only_keep` | asof | kept | **new** |
| `asof_empty_after_filter` | asof | empty | **new** |
| `gate_buy_high_risk_reject` | gate | reject | keep |
| `gate_hold_approve` | gate | approve | keep |
| `gate_pass_approve` | gate | approve | **new** |
| `gate_buy_below_threshold_approve` | gate | approve | **new** — just below live threshold |
| `gate_buy_at_threshold_reject` | gate | reject | **new** — `force_score ==` live threshold (`>=` policy) |
| `gate_determinism_twin` | gate | same_decision | **new** — twin inputs → identical decision |
| `oou_ticker_reject` | oou | reject | keep (TSLA or equiv) |
| `oou_second_reject` | oou | reject | **new** — second OOU symbol **or** fixture fail-closed |

- [ ] **B1.** Grow / rewrite `eval/golden_cases.jsonl` to **≥20** rows matching allocation **5/3/4/6/2** (sum ≥20; theme minima respected).  
- [ ] **B2.** Enrich sparse stubs in the same edit (`asof_drop_future`, `identity_overwrite`).  
- [ ] **B3.** Verify unique `case_id`s; every row has universal + per-`check` required keys.  
- [ ] **B4.** Ensure no case requires live Ollama, Kafka, or Option B train artifacts.  
- [ ] **B5.** Ensure no case asserts fixture F1 / Option B metrics.

### Phase C — Thin loader + check dispatch (`src/alphaguard/eval/`)

- [ ] **C1.** Move/share `load_golden_cases` into `src/alphaguard/eval/` (new module e.g. `loader.py` or `cases.py`; export from package `__init__` as appropriate). Prefer ≤300 lines/file.  
- [ ] **C2.** Implement fail-closed validation: missing `case_id`/`check`/`expect`; duplicate ids; optionally unknown `check` / missing per-check skeleton keys.  
- [ ] **C3.** Implement thin `check` → façade dispatch helpers (or keep dispatch inside the parametrized test module if still thin — loader **must** still live in package). Do **not** add a second orchestration stack / PipelineService E2E runner.  
- [ ] **C4.** Gate helpers: load fixture gate once (module-scoped fixture) and call `apply_policy` with `force_score`; derive boundary scores from live manifest.  
- [ ] **C5.** Update `tests/test_eval_stubs.py` (or successor) to import loader from `alphaguard.eval` — remove duplicate test-local-only loader as SSOT (test may keep a thin wrapper if needed).

### Phase D — Pytest parametrize + floor raise

- [ ] **D1.** Add parametrized test(s) that load all goldens and execute each `check` against façades; one failure → that `case_id` visible in pytest output.  
- [ ] **D2.** Raise presence assert from `len >= 5` to **`len >= 20`**.  
- [ ] **D3.** Assert theme coverage: at least the required checks present; optionally assert soft minima counts (schema≥3, identity≥2, asof≥3, gate≥4, oou≥2) and/or exact allocation if Implement freezes counts.  
- [ ] **D4.** Assert all `case_id`s unique.  
- [ ] **D5.** Keep existing unit tests (`test_contracts`, `test_gate`, `test_asof`, `test_fixtures`, …) — do not delete for “dedupe” in this guide.  
- [ ] **D6.** Confirm goldens do not require Kafka up or live Ollama.

### Phase E — Operator / interview honesty

- [ ] **E1.** Update README Limitations: eval grown to ≥20 **executed** goldens; still not live-Ollama numeric rates; still not Option B; still vertical slice / not v1 complete.  
- [ ] **E2.** Update INTERVIEW §15 (eval / invariants location): unit tests **and** ≥20 executable goldens; clarify structural schema checks ≠ live LLM pass-rate %.  
- [ ] **E3.** Optional one-liner in `AGENTS.md` if needed (“guide 03 eval harness landed”) — do not reopen stack locks.  
- [ ] **E4.** Do **not** tick VISION MV boxes; do **not** rewrite ARCHITECTURE §5/§12/§13 status prose as Align-docs (note lag only). Align-docs may refresh counts after Review.  
- [ ] **E5.** Grep for accidental “eval complete,” “portfolio-ready,” “Option B proven,” or “schema pass rate N%” live-Ollama claims; fix if introduced.

### Phase F — Verification + stop

- [ ] **F1.** Run verification commands in Definition of Done below; record evidence.  
- [ ] **F2.** Confirm smoke path / Makefile unchanged for Kafka requirement (Kafka still not required).  
- [ ] **F3.** Stop. Do not start Kafka E2E, Option B, packaging screenshot redo, Align-docs MV ticks, or replay-fixture ≥20 headline growth.

---

## Verification / Definition of Done (this guide)

**Done when all are true:**

1. `eval/golden_cases.jsonl` has **≥20** distinct `case_id`s covering themes per allocation (5/3/4/6/2 or ≥ minima with sum ≥20).  
2. Every row has universal keys + per-`check` skeleton payloads; sparse stubs enriched.  
3. `src/alphaguard/eval/` exports a fail-closed loader used by tests.  
4. Pytest **parametrizes** (or equivalent data-driven loop) and **executes** each golden against real façades.  
5. Presence/coverage floor is **`>= 20`** (+ theme asserts).  
6. README Limitations + INTERVIEW §15 updated for count + honesty (deferred live-Ollama rates / not Option B).  
7. Full unit suite green; no Kafka/Option B/live-Ollama rate DoD items claimed.  
8. No secrets committed; no VISION Align checkbox silent ticks; still vertical-slice language.

**Explicitly not required for this guide’s DoD:**

- Kafka E2E / Compose maturity  
- Option B train / U4 / real F1 claims  
- Live-Ollama numeric schema-pass % / 50-headline hold-out  
- Growing `replay_events.jsonl` to ≥20  
- Vol-veto goldens (optional only)  
- Packaging asset redo / LICENSE  
- Align-docs VISION / ARCHITECTURE §13 screenshot status ticks  
- Claiming eval-complete / portfolio-ready / v1 Done  
- Import-boundary arch tests (pass-12 overlooked; separate)  

**Suggested verification commands (implementer):**

```bash
# From alphaguard/
wc -l eval/golden_cases.jsonl                                    # ≥20
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter
rows=[json.loads(l) for l in Path("eval/golden_cases.jsonl").read_text().splitlines() if l.strip()]
ids=[r["case_id"] for r in rows]
assert len(rows) >= 20 and len(ids) == len(set(ids))
print(Counter(r["check"] for r in rows))
PY
uv run pytest tests/test_eval_stubs.py -q                        # or successor path
uv run pytest -q                                                 # full suite green
rg -n 'golden|≥20|>= 20|schema pass|Option B|fixture' README.md INTERVIEW.md
# Smoke path honesty (optional if unchanged): make smoke still must not require Kafka
```

---

## Blast radius and risks

| Risk | Blast radius | Mitigation in steps |
|------|----------------|---------------------|
| Count theater (+13 lines, no executor) | Interview credibility kill | Phases C–D require parametrize execution |
| Sparse-stub invent mid-Implement | Shape drift; flaky harness | Phase A skeleton + B2 enrich in same PR |
| Hardcoded `0.45` threshold | Float flake / wrong boundary story | A4 + C4 live manifest |
| Fixture F1 / Option B leakage | ML honesty kill | B5 + E5 bans |
| Live-Ollama scope creep | CI flake; calendar burn | Constraints + deferred DoD list |
| Parametrize × XGBoost load | Slow CI | Module-scoped gate; policy-only `force_score` |
| Duplicate truth vs unit tests | Maintainer confusion | Keep both; goldens thin; no mass-delete |
| Vol-veto vs fixture `false` | Confusing fails | Optional only; tmp manifest |
| Replay fixture ≥20 “while here” | Scope sprawl | Out of DoD (F3) |
| Kafka / Option B reopen | Hub ordering break | Stop conditions |
| INTERVIEW §15 / README stale | Interviewer confusion | Phase E |
| False “portfolio-ready” | Status theater | E5 + constraints |
| Allocation drift (15 schema, 1 asof) | Fake coverage | Soft recipe + D3 theme asserts |
| Raising floor before JSONL grown | Red CI mid-PR | Atomic PR or cases-first sequencing (B before D2) |
| VISION / ARCH §13 Align lag “fixed” here | Wrong owner | E4 Align-owned |

### Rollback

Eval JSONL + thin `src/alphaguard/eval/` + test/doc edits only. **Rollback** = revert the guide-03 commit(s); restore prior 7-stub JSONL + test-local loader if needed. No DB/migration/runtime flag. Do not leave README/INTERVIEW claiming ≥20 if code reverted.

---

## Edge-case handling (steps or DoD)

| Edge case | Expected guide-03 behavior |
|-----------|----------------------------|
| `available_at == published_at` | Keep hit (≤ filter) — golden asserts keep |
| `available_at` slightly after `published_at` | Drop — hard-fail if kept |
| Zero hits after as-of filter | Golden may assert emptiness only |
| LLM `event_id` + `ticker` both wrong | Stamp both from input |
| `SELL` in proposal | Schema reject — never approve / silent remap |
| OOU ticker | Fail closed (`ValidationError` / `FixtureLoadError`) |
| `BUY` score `== score_threshold` | Reject (`>=`) — include boundary golden |
| `BUY` just below threshold | Approve (absent vol veto) — include golden |
| `HOLD`/`PASS` with extreme score | Always approve |
| Confidence alone | Schema validates; gate must not change on confidence |
| Malformed JSONL line | Loader fail-closed → CI fail |
| Duplicate `case_id` | Reject / assert unique |
| Missing universal or skeleton keys | Fail closed at load |
| Vol veto + missing threshold | Existing GateLoadError — optional tmp-manifest golden only |
| CI without Ollama | Goldens must not require live LLM |
| Kafka up/down | Irrelevant to eval DoD |
| Naive datetime on hit | Good schema/asof candidate; contracts already unit-tested |
| Empty headline / confidence string | Schema theme fodder |
| Float threshold noise | Never assert `force_score == 0.45`; read manifest |
| Determinism twin | Same inputs → same gate decision |

---

## Stop conditions / non-goals

**Stop when** this guide’s DoD is met (executable ≥20 goldens + honesty docs).

**Do not:**

- Implement Kafka E2E, Option B train, U4, live-Ollama numeric rates, neural reranker, brokerage/Lowd  
- Grow replay fixture headlines to ≥20 “while here”  
- Redo packaging screenshots / FAQ sprawl beyond §15 honesty  
- Silently Align VISION MV checkboxes or ARCHITECTURE §13 “screenshots not present” lag  
- Claim eval-complete / portfolio-ready / v1 Done  
- Delete existing unit tests to “dedupe”  
- Flip committed fixture `vol_veto_enabled`  
- Proceed from Write → Ready-check / Implement without human gate  

If a stack or contract change seems required, **stop and ask** — eval harness must not reopen AG1–AG3 or VISION/ARCHITECTURE locks.

---

## Open decisions pinned (defaults)

| Decision | Pinned default | Tradeoff | Override |
|----------|----------------|----------|----------|
| Guide 03 = eval ≥20 (not Kafka / Option B) | **Yes** (pass-12) | Interview ROI; defers DE/ML maturity | Human reorders backlog |
| Harness = executable parametrized goldens | **Yes** | Slightly more code than JSONL-only | Human accepts theater (not recommended) |
| Theme allocation 5/3/4/6/2 | **Yes** | Balanced coverage | Human changes mix; keep minima |
| Loader in `src/alphaguard/eval/` | **Yes** | Small package surface | Human insists test-only (weaker) |
| Replay fixtures ≥20 in this guide | **No** | Keeps guide thin | Human expands |
| Vol-veto goldens required | **No** (optional) | One policy branch less golden-covered | Human requires |
| Align VISION / ARCH §13 mid-guide | **No** — separate Align-docs | Stale prose until Align | Human forces Align first |
| Kafka as guide 04 | **Open / hub** — note only | Does not block this Write | Hub decide later |

---

## Honest readiness (Write pass 28)

- **Write-dev-guide DoD:** met for this Draft (objective, learning notes, references, constraints, AC, ordered phases, DoD/verification, blast radius, edge cases, stop/non-goals/rollback, soft pins locked).  
- **Status:** **Draft — awaiting Ready check.** All Implement checkboxes remain `[ ]`.  
- **Not authorized:** Implement / code / JSONL growth / scrub.  
- **Not claimable:** eval-complete / portfolio-ready.  
- **Next human gate:** Ready-check (or Refine-dev-guide if gaps found) — then Implement only if READY.

### QUALITY_STANDARD §5 (this Write)

- [x] Assumptions replaced with pass-27 soft pins + context evidence  
- [x] Did not rush; did not implement; did not check Implement boxes  
- [x] Mode/Stage/artifacts declared (spoke Write-dev-guide pass 28)  
- [x] Edge cases + blast radius carried and executable in steps/DoD  
- [x] Findings written to this guide + handoff Results  
- [x] Spoke stayed in AlphaGuard eval slice; no Kafka/Option B/packaging redo  
- [x] Verification plan explicit; honest Draft status  
