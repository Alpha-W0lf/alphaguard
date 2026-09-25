# WP-ii-confirm — JH-63 path (ii) confirmatory eval (holdout B)

**Status:** COMPLETE · **FAIL** · model_quality_go_claimed=**false**
**Stamp:** 2026-09-25 05:52 PM CT (America/Chicago)
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b`
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)
**Routing:** Local · `OMP_NUM_THREADS=1` · workers=1 · no CloudAgent
**Uncommitted:** leave uncommitted

## Locked SSOT

| Item | Value |
|---|---|
| Pre-reg self-SHA256 | `5fbae0d07f50714211eb6a79a1e6b6fe1d5a5657f1e1959562d6338260514b6d` |
| Ticker-list canonical SHA256 | `1b107bb20f4f5b0d9cb9f4194cf320688be8d9654a9c2e4a084bc25e20a93f2f` |
| Holdout | **B** (20 expand tickers) |
| Rule | max F1 on inner-val **s.t. P≥0.25**; else no-operable-point Fail |
| Dataset hash | `2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528` |
| Geometry | boundary=189362 · train_end=188579 |
| Holdout B eval | n=**1925** · pos=**644** · base_rate=**0.334545** |
| Train after exclude | n=**154706** |
| Floors | F1≥0.30 · P≥0.25 · AUPRC≥0.18 (per seed on holdout B) |
| Served locked-test | regression only — not Go |

## Per-seed holdout B results

| Seed | Operable? | thr | val F1/P/R | Holdout F1 | P | R | AUPRC | P-lift | AUPRC-lift | Verdict | Failed |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 42 | yes | 0.25 | 0.1336/0.3489/0.0827 | 0.2824 | 0.3016 | 0.2655 | 0.3411 | 0.901× | 1.020× | **FAIL** | f1 (0.2824 < 0.3) |
| 7 | yes | 0.25 | 0.1270/0.3817/0.0761 | 0.2788 | 0.2995 | 0.2609 | 0.3400 | 0.895× | 1.016× | **FAIL** | f1 (0.2788 < 0.3) |
| 123 | yes | 0.25 | 0.1340/0.3504/0.0828 | 0.2239 | 0.2804 | 0.1863 | 0.3317 | 0.838× | 0.991× | **FAIL** | f1 (0.2239 < 0.3) |

**Study verdict: FAIL** (need all three seeds PASS).
**model_quality_go_claimed = false**

## Served locked-test (regression only — not Go)

| Seed | E4 published F1/P/AUPRC | This-run served F1/P/R/AUPRC (same thr) |
| ---: | --- | --- |
| 42 | 0.2460/0.1403/0.1648 | 0.2589/0.2019/0.3605/0.1801 |
| 7 | 0.2488/0.1421/0.1572 | 0.2311/0.1846/0.3090/0.1772 |
| 123 | 0.2467/0.1407/0.2031 | 0.2627/0.2128/0.3433/0.2117 |

## Anti-shopping

- One look only. No second threshold. No label change. No feature add. No ticker re-draw.
- Served locked-test never counted toward Go.
- Unconstrained F1-max was **not** used as fallback when eligible set empty.

## Artifacts

| Item | Path |
|---|---|
| This summary | `/Users/tom/Documents/Git/alphaguard-wt-option-b/runs/sample_expand_2026-09-25/wp-ii-confirm/summary.md` |
| Metrics JSON | `/Users/tom/Documents/Git/alphaguard-wt-option-b/runs/sample_expand_2026-09-25/wp-ii-confirm/metrics.json` |
| Runner | `/Users/tom/Documents/Git/alphaguard-wt-option-b/runs/sample_expand_2026-09-25/wp-ii-confirm/run_confirm_ii.py` |

## STOP

Fail stands. Publish honestly. No second look / threshold / ticker re-draw / floor move.
**Model Quality Go: UNCLAIMED.**
