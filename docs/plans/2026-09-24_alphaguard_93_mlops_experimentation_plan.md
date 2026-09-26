# AlphaGuard 9.3 — MLOps / Experimentation Plan

**Status:** Phase A **APPROVED** 2026-09-24 ~3:31 PM CT (Tom) — defaults: top-3, seeds [7,123], all floors hard; agent bc-1a92d234 implementing JH-AG-93.1  
**Author posture:** Job Hunt presents; this file is the sole deliverable for gate review  
**Title positioning:** Senior AI Engineer (Ex-Meta) — sell mastery without fabrication  
**Public voice:** noteworthy rigor; Fail stays Fail; lab metrics ≠ PnL / markets  
**Date:** 2026-09-24 (America/Chicago)

---

## 1. Goal

Raise AlphaGuard’s **portfolio display** to a **9.3+** bar across the audit dimensions Tom uses (Architecture, Durability, Tests/CI, Ops, Security, Simplicity, Presentation G/D/I/C/A), with WorkflowOS-style **approve-before-code** phases.

### What “done” means (three gates — do not collapse)

| Gate | Done means | Who claims |
|------|------------|------------|
| **Harness Go** | Parallel study runner, registry, compare, leakage guards, auto multi-seed promotion *logic*, smoke-in-CI, one-command reproduce — all work without cross-talk; tests green | Engineering (PR + CI) |
| **Model Quality Go (lab)** | Locked floors on freeze `534a341a…`: **F1 ≥ 0.30**, **P ≥ 0.25**, **AUPRC ≥ 0.18**, on seed 42 **and ≥ 2 extra seeds** with the same hparams; floors **still UNCLAIMED** as of this plan | **Human gate only** (Tom); harness may *propose* `candidate`, never auto-publish Go |
| **Economic / markets claim (future)** | Shadow vs rules, costs, slippage — **out of scope** for this plan; FINANCE_HONESTY forbids PnL fabrication | Explicit later ticket; not JH-63.* |

**Portfolio win condition for this track:** reviewers see a senior MLOps story — config-as-code studies, immutable run registry, honest Fail published, multi-seed discipline *in the harness*, clear promotion policy — **without** rewriting JH-63.1 Fail or claiming Model Quality Go prematurely.

---

## 2. Current state (Verified)

Explored Mac repo `/Users/tom/Documents/Git/alphaguard` (machine `75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`). Facts below are from git history, merged PRs, configs, artifacts, and docs — **no invented metrics**.

### Already Met (JH-63.*)

| Item | Evidence |
|------|----------|
| **JH-63.1 Fail published** | `docs/FINANCE_HONESTY.md` § JH-63.1; Fβ method B test F1=0.0 on tiny freeze; shipped default remains `train_f1_max`. PR **#4** merged (`JH-63.1: precision-weighted train-val threshold`). |
| **JH-63.2 parallel harness** | `scripts/run_study.py`, `scripts/compare_study.py`; `alphaguard.ml.study_{schema,runner,executor,registry,compare,cli,metrics,calibration,mlflow}`; ProcessPool; registry under `artifacts/runs/studies/<study_id>/`. PR **#5** (`feat(mlops): parallel experiment harness and run registry`). |
| **JH-63.3 freeze + re-baseline** | Full-pool freeze **n=8907**, `n_positive_test=233`, `dataset_hash=534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`; `train_f1_max` locked-test **F1≈0.2108**. Docs PR **#6**. JH-63.1 Fail **retained**. |
| **JH-63.4 docs voice** | PR **#7** (`docs(voice): implement JH-63.4 docs voice pass`). Product-led README; honesty in FINANCE_HONESTY / EXPERIMENTS. |
| **Study configs** | `configs/studies/jh63_2_smoke.yaml`, `jh63_matrix_c_8907.yaml`, `jh63_go_gate_seeds_7_123.yaml`. |
| **Harness tests** | `tests/test_study_harness.py` (~309 lines): parallel ≥2 configs, schema, isolation, leakage, hash mismatch, compare tables, metrics suite. |
| **CI baseline** | `.github/workflows/ci.yml` — `uv sync --frozen` + `pytest -q` on `main`/PRs. **No** study smoke job yet. |

### Matrix C + multi-seed (lab facts — Go unclaimed)

- **Matrix C** (`configs/studies/jh63_matrix_c_8907.yaml`): **96** cells, seed **42** only; Cartesian over threshold × beta × calibration × depth × scale_pos_weight (eta/rounds fixed). Artifact: `artifacts/runs/studies/jh63_matrix_c_8907/compare.md` (96 completed, 0 aborted, `promotion_decision: none`).
- **Best seed-42 cell:** F1≈**0.3658**, P≈**0.2787**, AUPRC≈**0.2087** (`run_065_be4e7afe_s42` / twin `run_089_…` — `train_val_fbeta_0.5`, isotonic, depth 2, spw 2, β 0.5/1.0 twin).
- **Locked lab Go floors (UNCLAIMED):** F1≥0.30, P≥0.25, AUPRC≥0.18, **plus ≥2 extra seeds beyond 42**.
- **Manual multi-seed gate FAIL** (`jh63_go_gate_seeds_7_123`): same winner hparams, seeds **7** and **123**. Study notes: seed 7 F1=0.2664 P=0.1711 AUPRC=0.1946; seed 123 F1=0.3227 P=0.2263 AUPRC=0.1963 — **precision mainly** breaks the P≥0.25 floor; neither pair clears “both extra seeds.” `promotion_decision` remains `none`.

### Gaps (honest — drive this backlog)

1. **Auto multi-seed promotion gate is not in the harness** — shortlist → extra seeds was a separate YAML / manual study. Belongs **inside** `run_study` / compare / parent `study.json` (Tom priority).
2. **Cartesian-only search** — Matrix C burned 96 cells on one freeze/seed; headroom should go to **seeds + smarter search**, not endless grids on the same freeze.
3. **Promotion policy** exists only as prose in EXPERIMENTS / FINANCE_HONESTY — no dedicated **lab Go vs ship vs markets** policy doc with machine-checkable statuses.
4. **CI does not run a smoke study** — unit harness tests only; no tiny fixture matrix in Actions.
5. **Registry promotion statuses** are `none | candidate | rejected` but **no automated writer** from floors + multi-seed rules; human still must claim Go.
6. **Dataset provenance / freeze tooling** is documented (hash fail-closed) but not packaged as a one-command “freeze + verify + register” operator path.
7. **README** sells product pipeline well; **EXPERIMENTS.md** sells the harness — still room to surface Fail-as-evidence and multi-seed discipline on the storefront without hype.
8. **Walk-forward / time-robust** and **economic shadow** stages are not implemented (correct for now).

---

## 3. Scorecard map (target 9.3 each)

Typical AlphaGuard / Job Hunt audit dims. Scores are **planning targets**, not a self-awarded audit. Honest ceilings noted where the lab nature of the product caps a dim.

| Dim | Target | Current posture (honest) | Work that moves the needle |
|-----|--------|---------------------------|----------------------------|
| **Architecture** | 9.3 | Strong: contracts, as-of, Option B gate ≠ analyst LLM; study modules cleanly layered | Auto multi-seed stage in runner; promotion state machine (propose ≠ claim); optional successive-halving *behind* YAML |
| **Durability** | 9.3 | Local registry + git/dataset/config hashes; ProcessPool isolation | Freeze tooling; reproduce one-command; registry schema version note; durable `candidate` records with seed rollups |
| **Tests / CI** | 9.3 | Good unit coverage for harness; CI = pytest only | Smoke study job (fixture / tiny synthetic matrix); tests for multi-seed gate pass/fail; compare asserts floors |
| **Ops** | 9.3 | CLI scripts + optional local MLflow file store | Documented operator runbook; CI smoke; wall-clock budgets; no cloud training dependency |
| **Security** | 9.3 | `.env` secrets; no keys in git; PolyForm-NC | Keep fail-open obs; no credential sprawl; hash fail-closed stays; refuse shipping secrets in study YAML |
| **Simplicity** | 9.3 | Cartesian expander is simple; risk is grid explosion | Prefer shortlist + auto seeds over mega-grids; successive halving optional Phase B — default path stays readable |
| **Presentation — G** (Goals / clarity) | 9.3 | VISION + FINANCE_HONESTY clear | Plan + promotion policy: three gates named; README pointer to EXPERIMENTS |
| **Presentation — D** (Evidence / depth) | 9.3 | Fail published; Matrix C + go-gate artifacts exist | Keep Fail; publish multi-seed discipline as *system* evidence; never polish metrics away |
| **Presentation — I** (Interview / narrative) | 9.3 | FAQ + Ex-Meta senior framing available | One crisp story: “we built the rails that caught seed fragility” |
| **Presentation — C** (Claim hygiene) | 9.3 | Explicit non-claims in FINANCE_HONESTY | Promotion policy doc; harness Go ≠ Model Quality Go baked into compare footers |
| **Presentation — A** (Aesthetics / storefront) | 9.0–9.3 | README product-led; EXPERIMENTS deeper | Light README link + compare.md polish; **ceiling ~9.3** without fake dashboards |

**Honest ceiling:** **Model Quality Go** may remain unclaimed for a long time; that must not block **Harness / portfolio 9.3**. Economic claim dim stays N/A until a future ticket.

---

## 4. Experimentation design

Stages are **sequential**; later stages consume shortlists from earlier ones. **No endless Cartesian on one freeze.**

```text
smoke  →  matrix / constrained search  →  auto multi-seed gate (shortlist)
       →  time-robust / walk-forward (lab)  →  (later) economic / shadow vs rules
```

### Stage 0 — Smoke
- Tiny matrix (existing `jh63_2_smoke.yaml` or CI fixture parquet): 2 seeds × 2 threshold methods × fixed shallow booster.
- Purpose: process isolation, registry write, compare generation, hash mismatch abort.
- **CI owns this** after Phase A.

### Stage 1 — Matrix / search (bounded)
- On freeze `534a341a…` only while this plan’s lab track runs.
- Prefer **narrow axes** (threshold method, calibration, depth, scale_pos_weight) with **seed=42** for discovery.
- **Budget rule:** if a proposed grid exceeds ~N cells (recommend **N ≤ 48** discovery + reserved seed budget), require Tom approve or switch to constrained / successive-halving (Phase B).
- Output: ranked shortlist (top-k by locked-test F1 with P/AUPRC reported — never hide confusion or n+).

### Stage 2 — Auto multi-seed gate (harness-native)
- For each shortlisted **hparams** (seed-agnostic config hash excluding seed): run **≥2 extra seeds** (default 7, 123; configurable).
- Evaluate locked floors **per seed**; parent study records rollup: `seeds_cleared`, `seeds_failed`, proposed `promotion_decision=candidate|rejected`.
- **Human** still claims Model Quality Go; harness only proposes.
- This stage is the **first implementation slice** after Approve (see §9).

### Stage 3 — Time-robust / walk-forward (lab)
- Expand beyond single nested split: rolling origin or blocked time folds **without** touching locked final holdout until freeze policy says so.
- Acceptance: documented fold metrics + variance; still **lab only**.

### Stage 4 — Economic / shadow (future — non-goal now)
- Shadow veto rate vs rules; costs/slippage — only after Model Quality Go and a separate honesty addendum.
- **Not** in Phase A–C of this plan.

### Headroom principle
Matrix C already spent 96 cells on seed 42. Further work on this freeze should **spend compute on seeds and smarter search**, not another 96-cell twin grid.

---

## 5. Harness / MLOps upgrades (phased backlog)

Concrete JH-style items. Effort: **S** / **M** / **L** (coarse). All require **Approve** before code.

### JH-AG-93.1 — Auto multi-seed promotion gate in study runner (**M** — first PR)
- **What:** After discovery runs (or via YAML `promotion: { shortlist_top_k, extra_seeds, floors }`), runner automatically schedules extra-seed cells for shortlisted hparams; writes seed rollup into `study.json`; compare.md shows pass/fail per floor.
- **Acceptance:**
  - Config can declare floors F1/P/AUPRC and `extra_seeds: [7,123]`.
  - Shortlist selection deterministic (documented sort keys).
  - Parent `promotion_decision` becomes `candidate` only if **all** required seeds clear floors; else `rejected` or stays `none` per policy.
  - Unit tests: synthetic shortlist where seed A passes / B fails → not `candidate`.
  - Docs: EXPERIMENTS + FINANCE_HONESTY note “propose ≠ claim.”
- **Non-acceptance:** Auto-editing FINANCE_HONESTY to claim Go; changing shipped default threshold method.

### JH-AG-93.2 — Promotion policy doc (**S**)
- **What:** `docs/PROMOTION_POLICY.md` — lab Go vs ship-default vs markets; human gate; harness statuses.
- **Acceptance:** Linked from EXPERIMENTS + FINANCE_HONESTY; three gates table mirrors §1; no PnL language.

### JH-AG-93.3 — Smoke study in CI (**S–M**)
- **What:** GitHub Actions job runs a **tiny** study on synthetic/fixture data (no Kaggle, no network), asserts registry files + compare exist + leakage tests already covered by pytest.
- **Acceptance:** PR CI red if smoke study fails; wall clock budget documented (target minutes, not hours); main pytest job unchanged.

### JH-AG-93.4 — Run registry + compare extensions (**S–M**)
- **What:** Seed-rollup fields; floor columns in compare; optional `shortlist.json`; schema version comment in study.json.
- **Acceptance:** Backward-compatible read of existing Matrix C artifacts; compare still shows confusion + n+.

### JH-AG-93.5 — Dataset provenance / freeze tooling (**M**)
- **What:** Operator script or documented `make freeze-verify` path: hash parquet, write freeze sidecar (hash, n, n_positive_test, label def, git SHA), refuse study if mismatch.
- **Acceptance:** Fail-closed demo in docs; JH-63.1 backup parquet path remains referenced.

### JH-AG-93.6 — Leakage guards audit (**S**)
- **What:** Checklist audit against `study_executor` / `train_option_b` + `tests/test_asof.py` / harness leakage tests; publish short AUDIT section in EXPERIMENTS or PROMOTION_POLICY.
- **Acceptance:** Explicit list of guards (test never in HPO/threshold/calib; as-of on features/retrieval); any gap → ticket, not silent skip.

### JH-AG-93.7 — Reproducibility one-command (**S**)
- **What:** Documented single command to re-run smoke study and regenerate compare from an existing study dir; pin `uv.lock` already present.
- **Acceptance:** Stranger clone path in GETTING_STARTED or EXPERIMENTS works without tribal knowledge (local parquet still required for full-pool — honesty note).

### JH-AG-93.8 — Docs / README sell harness mastery honestly (**S**)
- **What:** README “Deeper docs” bullet → EXPERIMENTS; one sentence that Fail published + multi-seed fragility is a **feature of the rails**.
- **Acceptance:** No new metric claims; Fail numbers untouched.

### JH-AG-93.9 — Successive halving / constrained search (**L** — optional Phase B)
- **What:** Optional search strategy to replace large Cartesians; keep YAML-declarative.
- **Acceptance:** Default path remains full Cartesian for small grids; large grids require explicit `search: successive_halving` (or similar); tests on toy grid.

### JH-AG-93.10 — Walk-forward stage scaffolding (**L** — Phase C)
- **What:** Study config axis or separate runner mode for time folds; registry stores fold metrics.
- **Acceptance:** Does not unlock economic claims; locked final holdout policy documented.

---

## 6. Data strategy

| Question | Guidance |
|----------|----------|
| **When to gather more events?** | After harness auto multi-seed + promotion policy land, **and** if multi-seed Fail persists under stronger search — then expand coverage (missing MSFT/SPY, longer calendar), not before fixing seed fragility process. |
| **Improve labels / features first?** | Label remains `fwd_return_5d < -0.03` unless Tom opens a labeled experiment with a **new freeze hash**. Feature work only with as-of discipline and a new study_id — never silent overwrite of `534a341a…`. |
| **Risk of scaling bad labels** | More rows with a weak or noisy downside definition **amplifies** overfit and false confidence (train/test F1 gap already ≈0.366 on re-baseline). Scale only with provenance sidecar + n_positive_test power notes. |
| **Current power** | n_positive_test=233 already clears JH-63.3 ≥30/≥50 power goals — **data volume is not the blocker** for the current Fail; **seed/precision stability** is. |

---

## 7. Non-goals

- Claiming **PnL**, brokerage edge, or Lowd Capital linkage.
- Rewriting or burying **JH-63.1 Fail** (or Matrix C / go-gate FAIL).
- Claiming **Model Quality Go** from this plan document or from harness `candidate`.
- **GPU** on Mac for this tabular XGBoost size (CPU seconds are fine).
- Duplicate **LinkedIn** packaging work / interview-branding reintroduction into the public README.
- Databricks / cloud training / mandatory MLflow SaaS.
- Endless Cartesian twin of Matrix C on the same freeze.
- Changing shipped default away from `train_f1_max` without a human Go + honesty table update.
- Economic shadow trading or cost models in Phase A–B.

---

## 8. Phased sequence (approve before code)

| Phase | Scope | Effort | Exit gate |
|-------|--------|--------|-----------|
| **Phase A — Rails** | JH-AG-93.1 auto multi-seed + 93.2 promotion policy + 93.4 compare/registry fields + 93.8 docs pointer | **M** (+ small S docs) | Tom Approve → implement → PR; harness tests + manual re-run of go-gate via new mechanism; **still no Model Quality Go claim** |
| **Phase B — CI & search** | 93.3 smoke-in-CI + 93.5 freeze tooling + 93.6 leakage audit + optional 93.9 successive halving | **M–L** | Approve separately; CI green on smoke study |
| **Phase C — Robustness** | 93.7 one-command polish + 93.10 walk-forward scaffolding; only then consider new data gather | **L** | Approve separately; lab-only metrics |

**Rule:** Job Hunt / Tom widget **Approve** on this plan before any Phase A code. Each later phase gets its own thin approve if scope drifts.

---

## 9. First PR after Approve

**Exactly one slice:** **JH-AG-93.1 — Auto multi-seed promotion gate** (plus minimal schema/compare hooks required for it). Defer successive halving, CI smoke study, and freeze CLI to Phase B unless Tom explicitly expands scope.

### Recommended PR shape
1. Extend `StudyMatrixConfig` / YAML with optional `promotion` block (floors, `extra_seeds`, `shortlist_top_k`, sort key).
2. After primary matrix completes (or `mode: promote_shortlist` on an existing study dir), expand shortlist × extra seeds, execute via existing ProcessPool path.
3. Write rollup on `ParentStudyRecord` (`promotion_decision`, notes, per-seed metrics summary).
4. Extend `compare.md` with a “Promotion gate” section.
5. Docs: EXPERIMENTS § promotion; link PROMOTION_POLICY if 93.2 lands in same PR or immediate follow-up.

### Test plan
- Unit: shortlist selection deterministic; floors helper pure functions.
- Unit: all extra seeds pass → `candidate`; any fail → not `candidate`.
- Unit/integration: existing Matrix C artifacts still load; no mutation of historical study dirs.
- Regression: `tests/test_study_harness.py` parallel + leakage still green.
- Manual (local): re-express `jh63_go_gate_seeds_7_123` via auto path; expect **FAIL/rejected** consistent with today’s notes — **proof the gate works**, not a Go claim.

---

## 10. Open decisions for Tom

1. **Shortlist size for auto multi-seed:** top-**1** vs top-**3** hparams from discovery (top-1 cheaper; top-3 catches near-ties like Matrix C twins).
2. **Extra seeds set:** keep **{7, 123}** as the locked pair vs add a third (e.g. 101) for stronger gate (more CPU, stricter).
3. **Floor application:** require **every** extra seed to clear **all three** floors vs allow one soft miss on AUPRC only (precision/F1 hard).
4. **Phase A docs:** PROMOTION_POLICY in the **same** PR as auto multi-seed vs **docs-only PR first** (approve-before-code comfort).
5. **CI smoke data:** synthetic frame in-repo vs tiny committed fixture parquet (license/size tradeoff; synthetic is simpler).
6. **Post-Fail model work:** after harness gate lands, next model attempt = **constrained re-search on same freeze** vs **feature/label rethink with new freeze** (do not do both at once).

---

## References (verified paths)

- Harness entrypoints: `scripts/run_study.py`, `scripts/compare_study.py`
- Modules: `src/alphaguard/ml/study_*.py`, `train_option_b.py`
- Configs: `configs/studies/jh63_*.yaml`
- Honesty / experiments: `docs/FINANCE_HONESTY.md`, `docs/EXPERIMENTS.md`, `docs/TRAINING_DATA.md`
- Artifacts: `artifacts/runs/studies/jh63_matrix_c_8907/`, `artifacts/runs/studies/jh63_go_gate_seeds_7_123/`
- Merged PRs: #4 (JH-63.1), #5 (JH-63.2 harness), #6 (JH-63.3 re-baseline docs), #7 (JH-63.4 voice)
- Freeze: `534a341a…` · n=8907 · n_positive_test=233 · re-baseline F1≈0.2108

---

*End of plan. No code changes authorized by this document alone.*
