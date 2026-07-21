# Review — AlphaGuard ticker alias registry FB→META + GOOG→GOOGL (pass 164n)

**Date:** 2026-07-21  
**Mode:** spoke  
**Stage:** Review implementation  
**Guide:** `docs/dev_guides/2026-07-21_dev_guide_thin_fb_meta_universe_alias.md` (Soft Adjust)  
**Implement:** `alphaguard@9724e00`  
**Handoff:** `second_brain/docs/2026-07-21_spoke_alphaguard_ticker_alias_review_pass164n_handoff.md`  
**Locks:** Tom authorize registry + parquet/Option B rebuild; declared MV stays Met (post-MV hygiene)

## Scope checked

Soft Adjust guide DoD vs `9724e00`: versioned registry `fb_meta_v1` + `goog_googl_v1`; default aliases on; `source_row_hash` on raw archive stock; `event_id` on post-alias ticker; Yahoo `FB`/`GOOG` hard-rejected on builder price path; provenance stats/logs; `builder_version=0.1.1`; join probe; unit tests on/off/no-fetch/fail-closed; TRAINING_DATA + FINANCE_HONESTY + ARCHITECTURE §7.1 honesty; local parquet + Option B rebuild evidence; no MSFT/SPY invent; live ingress still rejects raw `FB`/`GOOG`.

## Guide DoD verification

| Criterion | Evidence | Verdict |
|-----------|----------|---------|
| Registry coded, default on, toggleable off | `ARCHIVE_ALIAS_REGISTRY` + `apply_archive_aliases`; tests on/off | **Met** |
| Prices META/GOOGL only; FB/GOOG fetch guarded | `_reject_forbidden_price_ticker` in `default_yfinance_closes` + cached fetcher; unit tests | **Met** |
| Provenance + `builder_version` bump | `alias_rule_version` / `alias_applied_counts`; `BUILDER_VERSION=0.1.1` | **Met** |
| Tests: on, off, no FB/GOOG fetch, GOOG→GOOGL | `tests/test_dataset_build.py` alias suite | **Met** |
| Join probe (no invented closes / never FB) | `scripts/probe_fb_meta_join.py`; TRAINING_DATA `coverage=0.8953` | **Met** |
| Docs match code + rebuild metrics | TRAINING_DATA / FINANCE_HONESTY / §7.1 thin note | **Met** |
| Parquet + Option B regenerated | Local `training_events.parquet` META=71 GOOGL=86; manifest train F1≈0.693 test F1≈0.087 | **Met** |
| Character: post-MV; smoke fixture; no PnL/Guide 09 | No brokerage/MSFT-SPY invent; fixture smoke unchanged | **Met** |
| Live / fixtures still no silent remap | `NewsEvent` rejects `FB`/`GOOG`; replay OOU message intact | **Met** |

## Findings

| Severity | Finding | Tied to | Action |
|----------|---------|---------|--------|
| Soft | Fail-closed RuntimeError hardcodes `"META/GOOGL"` instead of deriving target tickers from the registry | Maintainability / QUALITY extensibility | Park — current registry is exactly those two; derive on next registry row |
| Soft | Unit test asserts `source_row_hash` for FB→META but not explicitly for GOOG→GOOGL (parity) | Guide C5 / edge completeness | Park — rebuild evidence: 60/86 GOOGL hashes fingerprint archive `GOOG` |
| Soft | No dedicated unit for native `META`+`FB` same-day headline dedup after alias | Guide edge-case table | Park — dedup subset is post-alias `(ticker, calendar_date, normalized_headline)`; behavior covered by general dedup |
| Soft | Holdout F1 weak/noisy (`n_positive_test=3`, test F1≈0.087) | Known honesty residual / blast radius | Honesty already documented — not a code defect |
| Soft | Guide status still Implement-oriented checkboxes; Review stamp optional | Align-docs | Hub Align if desired — not ship-blocker |

**Must-fix:** none.

## Architecture / quality

- Alias is **training ingest only** (`dataset_ingest`); contracts / RSS / fixtures unchanged — matches §7.1 “documented ≠ silent.”
- Forbidden price symbols derived from the same registry (`FORBIDDEN_PRICE_FETCH_TICKERS`) — single source of truth.
- `source_row_hash` uses raw `stock`; local parquet: **71/71** META rows fingerprint archive `FB`; GOOGL = 60 aliased `GOOG` + 26 native + **0 unexplained**.
- Files stay under ≤300 soft cap (`dataset_ingest.py` 289).
- No unrelated refactors; AG2/AG3 label/as-of path unchanged.

## Blast radius (Review re-check)

| Angle | Result |
|-------|--------|
| Wrong-asset Yahoo `FB` ETF | Guard + tests — residual only if someone bypasses builder fetcher |
| Metric drift after META/GOOGL enter sample | Expected; FINANCE_HONESTY updated same delivery |
| Live ingress accepting archive symbols | Still rejected by `NewsEvent` / universe |
| Future registry growth | Soft: fail message string should derive targets |

## Verification (Review)

```text
HEAD = 9724e00
uv run pytest -q → 109 passed, 6 deselected
parquet tickers: AAPL, AMZN, GOOGL(86), META(71), NVDA, QQQ; builder_version=0.1.1
manifest metrics match FINANCE_HONESTY (train F1≈0.693, test F1≈0.087)
NewsEvent(ticker=FB|GOOG) → ValidationError (OOU)
```

## Shippable call

**Shippable as-is.** No must-fix commit. Soft residuals are polish/park — do not block hub fan-in.

## Honest readiness

- **Ready for:** hub fan-in after Review; optional Align stamp on guide status.
- **Not ready because:** — (Review DoD Met)
- **Residuals:** weak holdout F1 honesty; MSFT/SPY still absent; Yahoo symbol remap risk over time.

## QUALITY self-check (§5)

- [x] Findings tied to guide / QUALITY_STANDARD  
- [x] Smallest fix set = none (shippable as-is justified)  
- [x] Edge cases + blast radius considered  
- [x] Spoke stayed in Review slice; no Implement of new features  
- [x] No open human decisions blocking Review  
- [x] Evidence from code, tests, parquet, manifest, docs  
