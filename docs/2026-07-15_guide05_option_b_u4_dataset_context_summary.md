# Context: Guide 05a — Option B dataset builder (U4-gated)

**Date:** 2026-07-15  
**Repos:** `alphaguard`  
**Status:** Refined (pass 59); **source locked 2026-07-16** (Kaggle — see pass 60)  
**Mode last used:** hub  
**Prioritize SSOT:** `second_brain/docs/2026-07-15_prioritize_next_work_pass58_fan_in.md`  
**Refine fan-in:** `second_brain/docs/2026-07-15_refine_context_pass59_fan_in.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`  
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

- **Plain title:** Which free training-news archive should AlphaGuard use for Option B? (id: H-AG-U4)
  - In plain terms: We need ~500 historical headlines with tickers and dates to build a training file. This is for offline model training, not a live news feed.
  - Options:
    - (A) Kaggle “Daily Financial News for 6000+ Stocks” (`miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests`) after you confirm license
    - (B) Free news API (Finnhub company news, Alpha Vantage news sentiment) — rate-limited; more glue code
    - (C) Another static free archive (e.g. Hugging Face FNSPID) after license skim
    - (D) Park Option B
  - Recommendation: **(A)** for training. Confirm license on Kaggle; builder downloads locally; do not commit the raw dump if license forbids; filter to the locked ticker list; sample ≈500.
  - Reasoning: Static historical CSV matches Option B (reproducible offline train). Papers cite coverage ~2009–2020 — **not live-updating**, which is fine for training. Fields `date` / `stock` / `headline` fit the builder. Live APIs add keys, rate limits, and backfill pain for little training benefit.
  - Tradeoffs: Archive is frozen history (no “fresh headlines every day”); day-level timestamps need careful as-of rules; you still must confirm license. Live RSS/API is a later product path, not this training slice.
- Split dataset builder vs model train into two guides — **recommended yes**.

## Evidence opened this pass

- ARCHITECTURE §11 / §6.3 / component table `ml/train`  
- VISION Option B row  
- Prioritize pass 58; Refine pass 59  
- Web skim: Kaggle massive-stock-news; FNSPID license caution  

## Honest readiness

- Ready for Write-dev-guide? **Yes** — Tom locked Kaggle source 2026-07-16. Guide must still record license text from the Kaggle page and timestamp/ticker/dedup policy.  
- Context quality after refine: **good enough** for Write-dev-guide.  
