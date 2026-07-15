# Context: Guide 05a — Option B dataset builder (U4-gated)

**Date:** 2026-07-15  
**Repos:** `alphaguard`  
**Status:** Refined (pass 59)  
**Mode last used:** hub  
**Prioritize SSOT:** `second_brain/docs/2026-07-15_prioritize_next_work_pass58_fan_in.md`  
**Refine fan-in:** `second_brain/docs/2026-07-15_refine_context_pass59_fan_in.md`  
**Role lens:** ML engineer + data engineer  

## Problem

Guides 01–04 shipped the replay vertical slice, packaging, eval goldens, and Kafka→Qdrant thin integration (including seek/commit + Compose proof). Agent 2 still loads a **`bundle_kind=fixture`** stub. VISION’s Option B row remains **Not started**; `data/training_events.parquet` is **absent**; `ml/train` is not started. Interviewers will correctly challenge “XGBoost gate” if the only bundle is fixture plumbing.

ARCHITECTURE §11 (**U4**) still requires a **human-selected** free CSV/Kaggle (or equivalent) financial-news source before an Option B training guide may claim a real dataset.

## Acceptance criteria

- [ ] Human **U4** decision recorded (source id, license/access, timestamp granularity, ticker mapping, duplicate policy) — AG-P1-5  
- [ ] Builder script produces ≈**500** rows filtered to locked ticker universe  
- [ ] Joins **yfinance** as-of features + **offline FinBERT** batch (not during smoke)  
- [ ] Writes `data/training_events.parquet` (+ documented regenerate path); large blobs not required in git  
- [ ] `resource_mode=finbert_train` honesty: prefer Kafka/Qdrant/Ollama down during FinBERT  
- [ ] Docs: VISION Option B row / ARCHITECTURE `ml/train` status updated same delivery — still not “v1 Done” until train metrics exist  
- [ ] Explicit: fixture bundle metrics are **not** Option B evidence  

## In scope

- U4 source lock (human) + dataset builder + parquet + FinBERT offline batch path  
- Thin README/training notes for regenerate  

## Out of scope

- XGBoost train / `bundle_kind=option_b` (Guide **05b**, depends on this parquet)  
- Live RSS reliability; Agent-on-consume; reopen Kafka Guide 04  
- Real LangSmith/Phoenix spans; cloud Kafka; brokerage; Lowd Capital  
- Option C (train on Agent 1 outputs)  

## Prior art (paths only)

- `docs/ARCHITECTURE.md` §6.3, §7.5, §11, §15–§16  
- `docs/VISION.md` Option B / MV checklist  
- `AGENTS.md` FinBERT offline-only  
- `scripts/build_fixture_bundle.py` (fixture only — not Option B)  
- Guide 04 context: `docs/2026-07-14_guide04_kafka_qdrant_integration_context_summary.md`  

## Risks and blast radius

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| License / redistributability of U4 source | Legal / public repo | Human records license; prefer public-domain / clearly licensed; avoid committing raw dumps if forbidden |
| Look-ahead / as-of leakage in joins | False ML story | Unified as-of UTC; AG3; document series |
| FinBERT + smoke stack RAM | Laptop thrash | `finbert_train` mode; stop Compose/Ollama when batching |
| Claiming Option B from fixture F1 | Interview honesty fail | Fail closed on `bundle_kind` mismatch; docs language |
| Scope creep into train+RSS | Guide bloat | Hard stop after parquet + FinBERT features |

## Edge cases

- Missing ticker / unmappable symbol → drop or quarantine with count  
- Duplicate headlines → documented dedup policy  
- Naive timestamps → reject or coerce to UTC with evidence  
- Partial FinBERT failure mid-batch → resume/idempotent rebuild  
- Empty parquet / &lt;500 after filters → honest shortfall + human decide  

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking? |
|---------|----------------|-----------|
| Exact U4 source (URL/Kaggle id) | **Human H-AG-U4** | **Yes** for Implement |
| Whether parquet is gitignored vs CI artifact | Write-dev-guide soft pin | No for Gather |
| Exact FinBERT model id already used offline | Read existing ml/ notes when writing guide | No |

## Recommended approach

1. Human locks **H-AG-U4** (source id + license + timestamp + ticker + dedup policy).  
2. Write-dev-guide: builder CLI, training-row schema (§7.5), FinBERT batch, verification commands.  
3. Implement builder only; **stop before** XGBoost train (05b).  

## Open decisions (human)

- **H-AG-U4**
  - Options: (A) soft-pin Kaggle `miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests` after license confirm; (B) FNSPID / other HF archive; (C) different free CSV after skim; (D) park Option B.
  - Recommendation: **(A)** — confirm license on the Kaggle page, then lock; builder downloads locally; do **not** commit raw dump if license forbids; filter to AG ticker universe; sample ≈500; UTC coerce policy documented.
  - Reasoning: Fields (`date`, `stock`, `headline`) match builder needs; widely used in NLP-backtest tutorials; aligns with ARCHITECTURE §11 “free CSV/Kaggle.” FNSPID notes commercial-use restrictions on code — worse fit for a public portfolio narrative.
  - Tradeoffs: Day-level timestamps may need careful as-of rules (AG3); license still human-verified (agent has not signed off legality); large download vs fixture-only path.
- Split Guide 05a vs 05b — **recommended yes** (pass 58). Unchanged.

## Evidence opened this pass

- ARCHITECTURE §11 / §6.3 / component table `ml/train`  
- VISION Option B row  
- Prioritize pass 58; Refine pass 59  
- Web skim: Kaggle massive-stock-news; FNSPID license caution  

## Honest readiness

- Ready for Write-dev-guide? **No** until **H-AG-U4** is locked (AG-P1-5). Soft-pin above is a recommendation, not a lock.  
- Context quality after refine: **good enough** once U4 is locked; no further Gather needed for 05a scope.  
