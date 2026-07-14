# Dev Guide 03 — Eval harness ≥21 goldens (+ vol-veto / fixture OOU / docs)

**Date:** 2026-07-14  
**Repo:** `alphaguard`  
**Work item:** Guide 03 — eval harness ≥21 goldens (executable, anti-theater; vol-veto + fixture-path OOU + docs alignment in DoD)  
**Stage that authored this:** Write-dev-guide (pass 28); Refine-dev-guide (pass 29–33)  
**Status:** **READY** (Ready check pass 35 — awaiting Implement authorize)

**Context SSOT:** `alphaguard/docs/2026-07-14_guide03_eval_harness_context_summary.md`  
**Prerequisite:** Guide 01 vertical slice shippable; Guide 02 interview packaging shippable (pass-24). This guide grows **eval goldens + thin harness** only — no Kafka, no Option B, no packaging redo.

---

## Objective

Grow the interview eval surface from a **7-stub count theater** to an **executable ≥21 golden harness**:

1. `eval/golden_cases.jsonl` — **≥21** distinct `case_id`s covering schema, identity overwrite, as-of/future-hit rejection, gate determinism, `SELL` reject, OOU reject (NewsEvent + fixture-path), and ≥1 tmp-manifest **vol-veto** golden (theme allocation **5 / 3 / 4 / 6 / 3** plus vol-veto coverage).  
2. Thin package loader under `src/alphaguard/eval/` — fail-closed on missing universal keys / duplicate ids; per-`check` payload keys from the frozen field skeleton.  
3. **Pytest parametrize** executes each golden against real public façades (`Agent1Proposal` / `NewsEvent` / `RetrievalHit`, `stamp_identity`, `filter_hits_as_of`, `apply_policy`) — a golden without an executor does **not** count.  
4. Raise presence/coverage floor from `>= 5` to **`>= 21`** + theme inventory asserts (incl. fixture-path OOU + vol-veto).  
5. Honesty docs — README Limitations + INTERVIEW §15 + **`AGENTS.md` one-liner** + VISION/ARCHITECTURE status language match new count; still **not** live-Ollama numeric schema-pass rates / not Option B metrics.

**Success signal:** `uv run pytest` green with ≥21 parametrized goldens executing (incl. fixture-path OOU + tmp-manifest vol-veto); reviewer can open JSONL + INTERVIEW + status docs and see honest “suite + goldens” without Kafka, Option B train, or LLM rate theater.

---

## Learning notes (new for this guide)

1. **Golden vs unit test** — A **unit test** hard-codes one scenario in Python. A **golden** is a data row (JSONL) that the same thin runner executes. Goldens are the interview-facing inventory (“here are 20 contracts we re-run”); unit tests stay for deep edges. Overlap is OK; do not delete `test_gate` / `test_asof` / `test_contracts` in this guide.

2. **Anti-theater / executable harness** — Counting lines in JSONL without running them is **count theater**. The harness is the small loader + `check` → façade map + pytest parametrize. If a row cannot execute, it does not satisfy DoD.

3. **Allocation recipe vs full inventory** — Pass 27 pinned **theme quotas** (how many of each `check`), not every `case_id` string. This guide freezes illustrative ids + the recipe as locked defaults; Implement may rename within a theme if counts/minima hold.

4. **Field skeleton as fail-closed design** — Universal keys (`case_id`, `check`, `expect`) plus per-`check` payload keys turn expect-only stubs into an explicit defect. Enrich sparse stubs in the **same** Implement PR as growth.

5. **Structural schema checks ≠ live-Ollama rates** — ARCHITECTURE §12 “schema pass rate” in this guide means **ok/reject counts on goldens**, never a CI percentage against a live LLM. Numeric LLM rates stay deferred (VISION Future / separate work).

6. **Expect protocol (oracle semantics)** — A golden without a frozen **assert map** still forces Implement invent. Inputs (`action`, `hits`, …) are not enough; each `check` + `expect` pair must name what the harness compares after the façade returns. Pass 29 freezes that map below.

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

1. **Eval growth + thin harness only.** No Kafka producer/consumer / `/trigger` / Compose maturity. No Option B `ml/train` / U4 / `training_events.parquet`. No packaging redo (`INTERVIEW` FAQ rewrite beyond §15 honesty, no new `docs/assets/`). **Do** update VISION / ARCHITECTURE / README / `AGENTS.md` status language in this same delivery so docs match shipped eval reality (trustworthy docs — not deferred Align theater).  
2. **AG1–AG3 locked** — goldens exercise contracts; do not soften them. ARCHITECTURE wins on wording conflicts.  
3. **Anti-theater:** every golden row must be executable via pytest parametrize against real façades. JSONL-only growth without a runner **fails DoD**.  
4. **Loader home:** `load_golden_cases` (and optional thin dispatch helpers) live under **`src/alphaguard/eval/`**; tests import the package — do not leave the only loader test-local forever.  
5. **Check dispatch map (frozen):**  
   - `schema` → `Agent1Proposal` / `NewsEvent` / `RetrievalHit` validation  
   - `identity` → `PipelineService.stamp_identity`  
   - `asof` → `filter_hits_as_of`  
   - `gate` → `DownsideRiskGate.apply_policy` (JSONL `force_score` → kwarg `downside_risk_score`; optional JSONL `volatility_20d` → `volatility_20d`; no live LLM; avoid XGBoost load per case when policy-only)  
   - `oou` → `NewsEvent` validator and/or fixture fail-closed  
6. **Do not** route goldens through full `PipelineService` orchestration / Kafka / live Ollama for numeric rates.  
7. **Fixture ≠ Option B:** never assert fixture `metrics.train_f1_at_threshold=1.0` as model quality; `bundle_kind=fixture` is plumbing only.  
8. **Threshold honesty:** read live `gate.manifest.score_threshold` (float noise ≈ `0.45000000000000007`); **never hardcode `0.45`** in asserts or boundary `force_score` construction.  
9. **Vol veto (required for this guide’s DoD):** committed fixture stays `vol_veto_enabled=false` / `vol_veto_threshold=null`. Implement **must** add ≥1 executable vol-veto golden via a **temporary (tmp) manifest** only — do **not** flip the committed fixture’s vol-veto flags.  
10. **Replay fixture headline growth to ≥20** (`data/fixtures/replay_events.jsonl`) is **out** (ARCHITECTURE §11 soft debt) unless human expands.  
11. **Keep existing unit tests**; goldens are additive data-driven coverage. Prefer ≤300 lines/file (hard max 400) for new eval modules.  
12. Still say **vertical slice / not v1 complete / not eval-complete / not portfolio-ready**.  
13. **Pass-12 lock (updated pass 33):** guide 03 = eval harness growth (not Kafka-first despite ARCHITECTURE §15 soft conflict). Cite override; do not rewrite §15 hard text in this guide. Floor target is **≥21** executed goldens per this guide’s DoD.

---

## Soft pins (locked defaults — do not reopen)

| Pin | Locked default |
|-----|----------------|
| Theme allocation | **schema 5 / identity 3 / asof 4 / gate 6 / oou 3 = 21**; soft minima 3/2/3/4/3; extras only on these themes (oou includes NewsEvent + fixture-path cases) |
| JSONL universal keys | Every row: `case_id` (unique), `check`, `expect` |
| JSONL field skeleton | Per-`check` keys in Phase A table (freeze; enrich sparse stubs) |
| Expect / assert protocol | Per-`check` oracle map below — **do not invent** assert shapes mid-Implement |
| Boundary `force_score` | String sentinels `"eq_threshold"` / `"just_below_threshold"` resolved from live manifest; epsilon **`1e-6`** |
| Determinism twin | **One** gate row; harness calls `apply_policy` **twice**; expect `same_decision` |
| Schema model default | `Agent1Proposal` unless optional `model` key says otherwise |
| Bad-field default | `schema_bad_confidence`: OOB **`confidence: 1.5`** (reject). Implement may swap to string confidence or empty rationale if still `reject` |
| Gate kwarg map | JSONL `force_score` → `apply_policy(..., downside_risk_score=...)`; JSONL `volatility_20d` (default `0.1`) → `volatility_20d` |
| Harness shape | JSONL ≥21 + **pytest parametrize** executing each `check` |
| Loader location | **`src/alphaguard/eval/`** |
| Loader fail-closed | Missing universal/skeleton keys, duplicate `case_id`, **unknown `check`** — all hard-fail |
| Floor assert | Raise `>= 5` → **`>= 21`** + theme coverage |
| Gate path | `apply_policy(action, force_score, vol)` preferred |
| Schema-pass wording | Structural golden ok/reject counts — **not** live-Ollama numeric rates |
| Hard bans | No Kafka; no Option B; no live-Ollama numeric schema-pass % in DoD |

### Soft-default theme allocation (total = 20)

| Theme (`check`) | Count | Soft minimum | Intent |
|-----------------|------:|-------------:|--------|
| `schema` | **5** | 3 | valid BUY; reject SELL; HOLD ok; PASS ok; one bad-field (**default** OOB `confidence: 1.5`) |
| `identity` | **3** | 2 | ticker overwrite; `event_id` overwrite; both mismatch stamped from input |
| `asof` | **4** | 3 | future drop; `available_at == published_at` keep; past-only keep; empty-after-filter |
| `gate` | **6** | 4 | BUY high→reject; HOLD→approve; PASS→approve; BUY below threshold→approve; BUY `== score_threshold`→reject; determinism twin |
| `oou` | **3** | 3 | (1) TSLA via `NewsEvent`; (2) NFLX via `NewsEvent`; (3) **required** fixture-load path OOU (`via: "fixture"` + `load_replay_events` / tmp JSONL) |
| **Total** | **20** | — | `SELL` reject lives under `schema` (`schema_reject_sell`); no parallel unsupported-action theme |

### Soft-default JSONL field skeleton

**Universal (every row):** `case_id`, `check`, `expect`. Loader **fail-closed** if any missing, `case_id` duplicates, or `check` not in `{schema,identity,asof,gate,oou}`. Missing per-`check` required keys → fail-closed (not warn/skip).

| `check` | Required payload keys | Optional / notes | Façade |
|---------|----------------------|------------------|--------|
| `schema` | `action`, `confidence` | Default model = **`Agent1Proposal`**. Optional `model`: `"Agent1Proposal"` \| `"NewsEvent"` \| `"RetrievalHit"`. Harness fills missing proposal fields with defaults: `rationale="golden"`, `event_id="evt-golden"`, `ticker="AAPL"` (override in JSONL when testing those fields). Bad-field default: **`confidence: 1.5`** (OOB → reject); string confidence or empty rationale allowed substitutes. | Per `model` |
| `identity` | `llm_ticker`, `input_ticker`, `llm_event_id`, `input_event_id` | Enrich existing stub (today tickers only). Harness builds `Agent1Proposal` from llm_* + defaults (`action="HOLD"`, `confidence=0.5`, `rationale="golden"`) and `NewsEvent` from input_* + defaults (`headline="golden"`, `source="fixture"`, `published_at="2024-03-12T14:30:00Z"`). Illustrative ids: overwrite stub → `llm_event_id="evt-llm"`, `input_event_id="evt-aapl-001"`; event-only → tickers both `AAPL`, ids differ; both-mismatch → tickers+ids both differ. | `PipelineService.stamp_identity` |
| `asof` | `published_at` (aware UTC ISO), `hits` (array) | Each hit: `document_id`, `text`, `ticker`, `available_at`, `source` (`fixture`\|`qdrant`); `score` optional (default `0.0`). **Recipe defaults** (reuse unit-test clock): `published_at="2024-03-12T14:30:00Z"`; past hit `available_at="2024-03-12T13:00:00Z"` `document_id="past"`; equal-boundary `available_at="2024-03-12T14:30:00Z"` `document_id="eq"`; future `available_at="2024-03-13T12:00:00Z"` `document_id="future"`; `ticker="AAPL"`, `text="golden"`, `source="fixture"`. | `filter_hits_as_of` |
| `gate` | `action`, `force_score` | `force_score` is a **number** or sentinel string `"eq_threshold"` \| `"just_below_threshold"`. Harness resolves sentinels from live `gate.manifest.score_threshold` (`eq` → exact threshold; `just_below` → `threshold - 1e-6`), then calls `apply_policy(action=..., downside_risk_score=<resolved>, volatility_20d=...)`. Optional `volatility_20d` (default `0.1`). Never hardcode `0.45`. Twin default: `action="BUY"`, `force_score=0.95`, `expect="same_decision"`. | `DownsideRiskGate.apply_policy` |
| `oou` | `ticker` | Default `via: "news_event"` (omit or set explicitly). Cases: (1) **`TSLA`** NewsEvent; (2) **`NFLX`** NewsEvent; (3) **required** `via: "fixture"` (tmp JSONL + `load_replay_events`) with a non-universe ticker. | `NewsEvent` (default) / fixture loader |

### Expect / assert protocol (frozen — harness oracle)

| `check` | Allowed `expect` | Harness assert after façade |
|---------|------------------|-----------------------------|
| `schema` | `ok` | Target model validates without error |
| `schema` | `reject` | Validation raises (`ValidationError` and/or `OutOfUniverseTickerError` when applicable) |
| `identity` | `stamped_from_input` | `stamped.ticker == input_ticker` **and** `stamped.event_id == input_event_id` (migrate legacy expect `"AAPL"` → this) |
| `asof` | `future_hit_dropped` | No kept hit has `available_at > published_at`; if input mixed past+future, at least one past hit remains |
| `asof` | `kept` | `len(filtered) == len(hits)` and document_id multiset unchanged |
| `asof` | `empty` | `len(filtered) == 0` |
| `gate` | `approve` / `reject` | `apply_policy(...)[0] == expect` (resolved `force_score` passed as `downside_risk_score`) |
| `gate` | `same_decision` | Call `apply_policy` twice with the same resolved `(action, downside_risk_score, volatility_20d)`; both `(decision, reason)` tuples equal |
| `oou` | `reject` | `NewsEvent` (or fixture load) raises fail-closed |

**Determinism twin (`gate_determinism_twin`):** single JSONL row with normal gate keys (`action="BUY"`, `force_score=0.95` defaults); **not** two rows and **not** a nested twin payload. Expect `same_decision` triggers the double-call assert above.

---

## Acceptance criteria (Implement must meet)

Copied/refined from context SSOT — do not invent extra scope:

- [ ] `eval/golden_cases.jsonl` contains **≥21** distinct `case_id`s (evidence: `wc -l` / JSON parse ≥21; unique ids)  
- [ ] Cases cover themes: **schema**, **identity** overwrite, **as-of** / future-hit rejection, **gate** determinism (BUY reject vs HOLD/PASS approve), **SELL** reject, **OOU** ticker reject (NewsEvent **and** fixture-path) — allocation **5/3/4/6/3** (or ≥ soft minima with sum ≥21)  
- [ ] **≥1 vol-veto golden** executes via **tmp manifest** only (committed fixture vol-veto flags unchanged)  
- [ ] Goldens are **not** count-only theater: pytest parametrize executes each case against real façades  
- [ ] `load_golden_cases` (or equivalent) lives under **`src/alphaguard/eval/`**; tests import it  
- [ ] Presence/coverage assert raises floor from `>= 5` to **`>= 21`** and asserts theme coverage / required checks present (incl. fixture-path OOU + vol-veto)  
- [ ] Sparse stubs enriched (`asof_drop_future` payloads; `identity_overwrite` gains event_id pair; identity `expect` → `stamped_from_input`)  
- [ ] Harness follows frozen **expect / assert protocol** + boundary `force_score` sentinels (no invent)  
- [ ] Documented **deferred**: live-Ollama numeric LLM schema-pass rate; Agent 1 hold-out on 50 headlines; Option B metrics; fixture-bundle F1 never quoted as model quality  
- [ ] No Kafka; no Option B / U4 / `ml/train`; no packaging redo  
- [ ] README Limitations + INTERVIEW §15 + **`AGENTS.md` one-liner** updated; **VISION / ARCHITECTURE status language** updated in this same delivery to match ≥21 executed goldens (trustworthy docs — no stale “≥5 stub” claims)  
- [ ] Existing unit tests remain green; smoke path unchanged (Kafka still not required)  

---

## Ordered step checklist

All boxes start unchecked. Implement checks them with evidence. **Do not check boxes in Write / Ready-check.**

### Phase A — Freeze JSONL contract + enrich plan

- [ ] **A1.** Confirm `eval/golden_cases.jsonl` baseline is still **7** unique rows before edits (`wc -l` + parse).  
- [ ] **A2.** Freeze universal keys + per-`check` skeleton + **expect / assert protocol** from Soft pins (do not reopen). Loader fail-closed: missing universal/skeleton key, duplicate `case_id`, unknown `check`.  
- [ ] **A3.** Plan enrichment for existing sparse rows:  
  - `asof_drop_future` — add `published_at` + `hits` (mixed past + future; expect `future_hit_dropped`)  
  - `identity_overwrite` — add `llm_event_id` + `input_event_id`; migrate `expect` from `"AAPL"` → **`stamped_from_input`**  
- [ ] **A4.** Confirm gate boundary cases use `force_score` sentinels `"eq_threshold"` / `"just_below_threshold"` resolved from live manifest (`just_below` = `threshold - 1e-6`); no hardcoded `0.45`.  
- [ ] **A5.** Plan **required** vol-veto golden(s) with this **pinned recipe** (pass 37):  
  - Copy `data/fixtures/model_bundle_fixture/{manifest.json,model.json}` into a pytest `tmp_path` bundle dir (same pattern as `tests/test_gate.py` skewed-manifest test).  
  - In the **tmp** `manifest.json` only: set `vol_veto_enabled=true` and `vol_veto_threshold=0.05` (do **not** edit committed fixture).  
  - Construct `DownsideRiskGate(tmp_bundle_dir)`.  
  - Call `apply_policy(action="BUY", downside_risk_score=<resolved force_score below score_threshold e.g. "just_below_threshold">, volatility_20d=0.20)` so veto fires (`volatility_20d >= 0.05`) while score alone would approve.  
  - JSONL row: `case_id=gate_vol_veto_reject`, `check=gate`, `expect=reject`, plus optional harness-only flag `tmp_vol_veto=true` (or detect by `case_id`) so dispatch uses tmp gate — do **not** flip committed fixture flags.  
- [ ] **A6.** Plan **required** fixture-path OOU case with this **pinned recipe** (pass 37):  
  - Write tmp JSONL with **one** `NewsEvent`-shaped line: `event_id`, `headline`, `ticker="TSLA"` (OOU), `source="fixture"`, `published_at` ISO-Z (mirror `replay_events.jsonl` shape).  
  - Harness calls `load_replay_events(tmp_path)` and expects `FixtureLoadError` **or** `OutOfUniverseTickerError` / validation fail-closed (whatever `load_replay_events` raises today — do not soften).  
  - JSONL: `case_id=oou_fixture_path_reject`, `check=oou`, `via="fixture"`, `ticker="TSLA"`, `expect=reject`.  
- [ ] **A7.** Confirm determinism twin is **one row** + double `apply_policy` (expect `same_decision`) — not a nested twin payload.

### Phase B — Author ≥21 goldens (allocation recipe)

**Illustrative `case_id` inventory (Implement may rename within theme if counts hold):**

| `case_id` | `check` | `expect` (illustrative) | Notes |
|-----------|---------|-------------------------|-------|
| `schema_valid_buy` | schema | ok | keep; harness defaults for rationale/event_id/ticker OK |
| `schema_reject_sell` | schema | reject | keep (`SELL`) |
| `schema_hold_ok` | schema | ok | **new** |
| `schema_pass_ok` | schema | ok | **new** |
| `schema_bad_confidence` | schema | reject | **new** — default OOB `confidence: 1.5` (string confidence / empty rationale OK substitutes) |
| `identity_overwrite` | identity | stamped_from_input | **enrich** `llm_event_id`/`input_event_id` (defaults `evt-llm` / `evt-aapl-001`); migrate expect off bare `"AAPL"` |
| `identity_event_id_overwrite` | identity | stamped_from_input | **new** — tickers both `AAPL`; event_ids differ |
| `identity_both_mismatch` | identity | stamped_from_input | **new** |
| `asof_drop_future` | asof | future_hit_dropped | **enrich** per asof recipe (past + future hits) |
| `asof_equal_boundary_keep` | asof | kept | **new** — `available_at == published_at` (recipe `eq` hit) |
| `asof_past_only_keep` | asof | kept | **new** — past hit(s) only |
| `asof_empty_after_filter` | asof | empty | **new** — all hits future |
| `gate_buy_high_risk_reject` | gate | reject | keep (`force_score` numeric e.g. `0.95`) |
| `gate_hold_approve` | gate | approve | keep |
| `gate_pass_approve` | gate | approve | **new** |
| `gate_buy_below_threshold_approve` | gate | approve | **new** — `force_score: "just_below_threshold"` |
| `gate_buy_at_threshold_reject` | gate | reject | **new** — `force_score: "eq_threshold"` |
| `gate_determinism_twin` | gate | same_decision | **new** — single row; defaults `BUY` + `0.95`; double-call assert |
| `oou_ticker_reject` | oou | reject | keep (`ticker=TSLA`, NewsEvent) |
| `oou_second_reject` | oou | reject | **new** — `ticker=NFLX` (NewsEvent) |
| `oou_fixture_path_reject` | oou | reject | **new / required** — `via: "fixture"` + non-universe ticker via `load_replay_events` |
| `gate_vol_veto_reject` | gate | reject | **new / required** — tmp manifest vol-veto path (committed fixture unchanged) |

- [ ] **B1.** Grow / rewrite `eval/golden_cases.jsonl` to **≥21** theme rows matching allocation **5/3/4/6/3**, **plus** ≥1 vol-veto golden (may be a 22nd row if cleaner — DoD is themes ≥21 **and** vol-veto present). Expects from the frozen protocol.  
- [ ] **B2.** Enrich sparse stubs in the same edit (`asof_drop_future`, `identity_overwrite` + expect migrate).  
- [ ] **B3.** Verify unique `case_id`s; every row has universal + per-`check` required keys; boundary gates use sentinels not `0.45`.  
- [ ] **B4.** Ensure no case requires live Ollama, Kafka, or Option B train artifacts.  
- [ ] **B5.** Ensure no case asserts fixture F1 / Option B metrics.

### Phase C — Thin loader + check dispatch (`src/alphaguard/eval/`)

- [ ] **C1.** Move/share `load_golden_cases` into `src/alphaguard/eval/` (new module e.g. `loader.py` or `cases.py`; export from package `__init__` as appropriate). Prefer ≤300 lines/file.  
- [ ] **C2.** Implement fail-closed validation: missing `case_id`/`check`/`expect`; duplicate ids; **unknown `check`**; missing per-check skeleton keys.  
- [ ] **C3.** Implement thin `check` → façade dispatch helpers (or keep dispatch inside the parametrized test module if still thin — loader **must** still live in package). Follow **expect / assert protocol** exactly. Do **not** add a second orchestration stack / PipelineService E2E runner.  
- [ ] **C4.** Gate helpers: load fixture gate once (module-scoped fixture); resolve `force_score` sentinels from live manifest; map to `downside_risk_score` kwarg; call `apply_policy`; for `same_decision`, double-call and compare tuples.  
- [ ] **C5.** Update `tests/test_eval_stubs.py` (or successor) to import loader from `alphaguard.eval` — remove duplicate test-local-only loader as SSOT (test may keep a thin wrapper if needed).

### Phase D — Pytest parametrize + floor raise

- [ ] **D1.** Add parametrized test(s) that load all goldens and execute each `check` against façades; one failure → that `case_id` visible in pytest output.  
- [ ] **D2.** Raise presence assert from `len >= 5` to **`len >= 21`**.  
- [ ] **D3.** Assert theme coverage: required checks present; **assert soft minima** (schema≥3, identity≥2, asof≥3, gate≥4, oou≥3) and fixture-path OOU + vol-veto coverage present.  
- [ ] **D4.** Assert all `case_id`s unique.  
- [ ] **D5.** Keep existing unit tests (`test_contracts`, `test_gate`, `test_asof`, `test_fixtures`, …) — do not delete for “dedupe” in this guide.  
- [ ] **D6.** Confirm goldens do not require Kafka up or live Ollama.

### Phase E — Operator / interview honesty

- [ ] **E1.** Update README Limitations: eval grown to ≥21 **executed** goldens (incl. fixture-path OOU + tmp-manifest vol-veto); still not live-Ollama numeric rates; still not Option B; still vertical slice / not v1 complete.  
- [ ] **E2.** Update INTERVIEW §15 (eval / invariants location): unit tests **and** ≥21 executable goldens; clarify structural schema checks ≠ live LLM pass-rate %.  
- [ ] **E3.** Add **required** one-liner in `AGENTS.md` (“guide 03 eval harness landed — ≥21 executable goldens”) — do not reopen stack locks.  
- [ ] **E4.** Update VISION / ARCHITECTURE status language in **this same delivery** so checkboxes/prose match ≥21 executed goldens (trustworthy docs). Do **not** claim Kafka / Option B / live-Ollama rates done.  
- [ ] **E5.** Grep for accidental “eval complete,” “portfolio-ready,” “Option B proven,” or “schema pass rate N%” live-Ollama claims; fix if introduced.

### Phase F — Verification + stop

- [ ] **F1.** Run verification commands in Definition of Done below; record evidence.  
- [ ] **F2.** Confirm smoke path / Makefile unchanged for Kafka requirement (Kafka still not required).  
- [ ] **F3.** Stop. Do not start Kafka E2E, Option B, packaging screenshot redo, or replay-fixture ≥20 headline growth.

---

## Verification / Definition of Done (this guide)

**Done when all are true:**

1. `eval/golden_cases.jsonl` has **≥21** distinct `case_id`s covering themes per allocation (5/3/4/6/3 or ≥ minima with sum ≥21), including fixture-path OOU.  
2. Every row has universal keys + per-`check` skeleton payloads; sparse stubs enriched; expects match the frozen assert protocol.  
3. `src/alphaguard/eval/` exports a fail-closed loader used by tests (unknown check / missing skeleton keys hard-fail).  
4. Pytest **parametrizes** (or equivalent data-driven loop) and **executes** each golden against real façades per expect protocol (including sentinel `force_score` resolution + twin double-call + tmp-manifest vol-veto + fixture-path OOU).  
5. Presence/coverage floor is **`>= 21`** (+ theme asserts incl. oou≥3, vol-veto present).  
6. README Limitations + INTERVIEW §15 + **`AGENTS.md` one-liner** updated for count + honesty (deferred live-Ollama rates / not Option B).  
7. **VISION / ARCHITECTURE status language** updated in the same delivery to match ≥21 executed goldens (trustworthy docs).  
8. Full unit suite green; no Kafka/Option B/live-Ollama rate DoD items claimed.  
9. No secrets committed; still vertical-slice language (no false “v1 complete”).

**Explicitly not required for this guide’s DoD:**

- Kafka E2E / Compose maturity  
- Option B train / U4 / real F1 claims  
- Live-Ollama numeric schema-pass % / 50-headline hold-out  
- Growing committed `replay_events.jsonl` headline count to ≥20 (tmp fixture-path OOU JSONL is in DoD)  
- Packaging asset redo / LICENSE  
- Claiming eval-complete / portfolio-ready / v1 Done  
- Import-boundary arch tests (pass-12 overlooked; separate)  

**Suggested verification commands (implementer):**

```bash
# From alphaguard/
wc -l eval/golden_cases.jsonl                                    # ≥21
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter
rows=[json.loads(l) for l in Path("eval/golden_cases.jsonl").read_text().splitlines() if l.strip()]
ids=[r["case_id"] for r in rows]
assert len(rows) >= 21 and len(ids) == len(set(ids))
print(Counter(r["check"] for r in rows))
assert any(r.get("case_id") == "oou_fixture_path_reject" for r in rows)
assert any(r.get("case_id") == "gate_vol_veto_reject" or "vol_veto" in r.get("case_id","") for r in rows)
PY
uv run pytest tests/test_eval_stubs.py -q                        # or successor path
uv run pytest -q                                                 # full suite green
rg -n 'golden|≥21|>= 21|schema pass|Option B|fixture|vol.veto|vol_veto' README.md INTERVIEW.md AGENTS.md docs/VISION.md docs/ARCHITECTURE.md
# Smoke path honesty (optional if unchanged): make smoke still must not require Kafka
```

---

## Blast radius and risks

| Risk | Blast radius | Mitigation in steps |
|------|----------------|---------------------|
| Count theater (+13 lines, no executor) | Interview credibility kill | Phases C–D require parametrize execution |
| Sparse-stub invent mid-Implement | Shape drift; flaky harness | Phase A skeleton + expect protocol + B2 enrich in same PR |
| Hardcoded `0.45` threshold | Float flake / wrong boundary story | A4 sentinels + C4 live manifest |
| Ambiguous `expect` / twin shape | Harness invent; flaky oracles | Frozen expect protocol + single-row twin |
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
| VISION / ARCH status lag after eval growth | Untrustworthy docs | E4 same-delivery status update (pass 33) |

### Rollback

Eval JSONL + thin `src/alphaguard/eval/` + test/doc edits only — **no DB / migration / runtime flag**.

**Executable rollback:**

1. `git revert` (or reset) the guide-03 Implement commit(s).  
2. Confirm restored paths match pre-guide-03 baseline:  
   - `eval/golden_cases.jsonl` → **7** stub rows (test-local loader still works)  
   - `src/alphaguard/eval/` → docstring-only package (or remove added modules)  
   - `tests/test_eval_stubs.py` → test-local `load_golden_cases` + `len >= 5`  
   - `README.md` / `INTERVIEW.md` §15 → stub/≥5 honesty (not “≥20 executed”)  
3. `uv run pytest -q` green on restored tree.  
4. Do **not** leave README/INTERVIEW claiming ≥20 if code reverted.

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
| `BUY` score `== score_threshold` | Reject (`>=`) — golden uses `force_score: "eq_threshold"` |
| `BUY` just below threshold | Approve (absent vol veto) — `force_score: "just_below_threshold"` (`threshold - 1e-6`) |
| `HOLD`/`PASS` with extreme score | Always approve |
| Confidence alone | Schema validates; gate must not change on confidence |
| Malformed JSONL line | Loader fail-closed → CI fail |
| Duplicate `case_id` | Reject / assert unique |
| Missing universal or skeleton keys | Fail closed at load |
| Unknown `check` | Fail closed at load |
| Vol veto + missing threshold | Existing GateLoadError — tmp-manifest golden must cover happy/veto path with valid threshold |
| CI without Ollama | Goldens must not require live LLM |
| Kafka up/down | Irrelevant to eval DoD |
| Naive datetime on hit | Good schema/asof candidate; contracts already unit-tested |
| Empty headline / confidence string | Schema theme fodder |
| Float threshold noise | Never assert `force_score == 0.45`; use sentinels / read manifest |
| Determinism twin | Same resolved inputs → same `(decision, reason)` via double-call |
| Legacy identity expect `"AAPL"` | Migrate to `stamped_from_input` when enriching |

---

## Stop conditions / non-goals

**Stop when** this guide’s DoD is met (executable ≥21 goldens + vol-veto + fixture-path OOU + honesty docs).

**Do not:**

- Implement Kafka E2E, Option B train, U4, live-Ollama numeric rates, neural reranker, brokerage/Lowd  
- Grow replay fixture headlines to ≥20 “while here”  
- Redo packaging screenshots / FAQ sprawl beyond §15 honesty  
- Silently Align VISION MV checkboxes or ARCHITECTURE §13 “screenshots not present” lag  
- Claim eval-complete / portfolio-ready / v1 Done  
- Delete existing unit tests to “dedupe”  
- Flip committed fixture `vol_veto_enabled`  
- Proceed from Refine → Ready-check / Implement without human gate  

If a stack or contract change seems required, **stop and ask** — eval harness must not reopen AG1–AG3 or VISION/ARCHITECTURE locks.

---

## Open decisions pinned (defaults)

| Decision | Pinned default | Tradeoff | Override |
|----------|----------------|----------|----------|
| Guide 03 = eval ≥20 (not Kafka / Option B) | **Yes** (pass-12) | Interview ROI; defers DE/ML maturity | Human reorders backlog |
| Harness = executable parametrized goldens | **Yes** | Slightly more code than JSONL-only | Human accepts theater (not recommended) |
| Theme allocation 5/3/4/6/3 (≥21) | **Yes** (pass 33 human) | Adds fixture-path OOU | Human changes mix; keep minima |
| Expect / assert protocol | **Yes** (pass 29) | Slightly more guide prose | Human accepts invent (not recommended) |
| Boundary force_score sentinels | **Yes** (`eq` / `just_below`, ε=`1e-6`) | Avoids hardcoded 0.45 | Human picks different ε |
| Gate kwarg map (`force_score` → `downside_risk_score`) | **Yes** (pass 30) | Matches live `apply_policy` | Human renames JSONL key (not recommended) |
| Bad-field / asof / twin recipes | **Yes** (pass 30 defaults) | Less invent; still not full JSONL dump | Human prefers different strings |
| Determinism twin = single-row double-call | **Yes** | No nested twin schema | Human wants two linked rows |
| OOU coverage | **TSLA + NFLX NewsEvent + required fixture-path** | Broader fail-closed paths | Human drops one path |
| Loader in `src/alphaguard/eval/` | **Yes** | Small package surface | Human insists test-only (weaker) |
| Replay fixtures ≥20 in committed file | **No** | Keeps guide thin | Human expands |
| Vol-veto goldens required | **Yes** (pass 33; tmp manifest only) | Covers veto branch without flipping committed fixture | Human drops coverage |
| AGENTS.md one-liner | **Yes** (pass 33) | Small operator signal | Human rejects |
| Update VISION / ARCHITECTURE status in same delivery | **Yes** (pass 33; trustworthy docs) | Docs match shipped eval | Human parks Align explicitly |
| Kafka as guide 04 | **Open / hub** — note only | Does not block this guide | Hub decide later |

---

## Honest readiness (pass 37 VERIFY)

- **Implement readiness score:** **9.4 / 10** — pass 37 pinned concrete vol-veto tmp-bundle recipe + fixture-path OOU JSONL recipe (closes remaining harness invent). **Not 10:** remaining schema/asof/identity/gate theme rows still authored from soft-default recipes (not a full JSONL dump).  
- **Status:** **READY** — awaiting Implement authorize. Live tree still baseline (7 JSONL stubs; loader test-local; floor `>= 5`).  
- **Not authorized:** Implement until human says so.  
- **Still soft (non-blocking):** exact non-vol/non-fixture-OOU JSONL payloads; Kafka-as-04 hub note.  

### Prior scores

- Pass 36: **9.1** · Pass 33: **9.0**

### QUALITY_STANDARD §5 (this VERIFY)

- [x] Live baselines re-verified (7 goldens; vol_veto_enabled=false; score_threshold float noise; test-local loader)  
- [x] Material invent gaps closed with evidence from `gate.py` / `test_gate.py` / `replay.py` / `TICKER_UNIVERSE`  
- [x] No Implement; scores not inflated  
