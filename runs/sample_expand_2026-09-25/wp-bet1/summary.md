# JH-63 Bet 1 — OOF precision-wall diagnosis

**Status:** COMPLETE · diagnosis only · **Go UNCLAIMED**  
**Locked:** 2026-09-25 ~5:17 PM CT (Tom) · run finished ~5:25 PM CT  
**Machine:** Toms-MB-Pro-M2-Pro (`75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`)  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b` @ `main` / option-b lineage  
**Spec SSOT:** `/Users/tom/Documents/Git/custom_resumes/docs/backlog/2026-09-25_jh63_post_e4_experiment_matrix_strategy.md` §4 Bet 1  
**Routing:** local · Mac free · new · Opus plan yes · why cloud: n/a local · workers=1  

## Claims discipline

- Diagnosis only. **No Go claim.** No floor / feature / volume shopping.
- Locked-test numbers below are **quoted from published E4** only (never re-scored).
- All new metrics are **expanding4 purged OOF** on train/dev. Locked-test rows are outside OOF indices.

## Freeze

| Item | Value |
|---|---|
| Dataset study hash | `2e8db9a9ac77975ee7a88ec828748afe70827f50a1a4ee7c5709dde35a8c8528` |
| File | `data/derived/training_events_jh63e_ecb73eca.parquet` (n=201255) |
| Label | −3% / 5d (`label_high_risk`) |
| Features (9) | finbert_sentiment · volatility_20d · return_5d_prior · return_20d_prior · spy_return_5d · rs_20d · drawdown_20d · volatility_5d · spy_volatility_20d |
| Seeds | 42 / 7 / 123 |
| XGB | max_depth=2 · eta=0.1 · rounds=40 · scale_pos_weight=2 · subsample/colsample=0.8 · isotonic cal · nthread=1 |
| Floors (reference only) | F1≥0.30 · P≥0.25 · AUPRC≥0.18 — **not a pass gate here** |

### OOF fold geometry (date-anchor + trading-day embargo)

- Locked-test boundary = 189362 · purged `train_end` = 188579  
- OOF val span = 113148 rows / 18805 pos (prevalence **0.1662**)  
- Expanding4 purged folds on train/dev only:

| Fold | Train | Val | Embargo |
| ---: | --- | --- | ---: |
| 0 | [0:74884) | [75431:103718) | 547 |
| 1 | [0:103215) | [103718:132005) | 503 |
| 2 | [0:131378) | [132005:160292) | 627 |
| 3 | [0:159899) | [160292:188579) | 393 |

Feature groups:

| Group | Members |
|---|---|
| **text** | finbert_sentiment |
| **price** | volatility_20d, return_5d_prior, return_20d_prior, rs_20d, drawdown_20d, volatility_5d |
| **calendar** | spy_return_5d, spy_volatility_20d *(no DOW/month in freeze; spy_* = market/regime proxy)* |

---

## 1. Baselines (OOF)

| Model | Seed | AUPRC | Brier | F1@F1-max | P@F1-max | R@F1-max | max P @ R≥0.375 |
|---| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Flag-everything** | — | =prev 0.166 | — | **0.2850** | 0.1662 | 1.000 | 0.1662 |
| **LogReg** | all | **0.2274** | ~0.137 | 0.3163 | 0.2159 | 0.592 | **0.2407** |
| **XGB** | 42 | 0.2273 | 0.1369 | 0.3126 | 0.2173 | 0.557 | **0.2411** |
| **XGB** | 7 | 0.2277 | 0.1370 | 0.3158 | 0.2214 | 0.550 | **0.2357** |
| **XGB** | 123 | 0.2268 | 0.1370 | 0.3138 | 0.2168 | 0.568 | **0.2405** |
| **XGB mean** | — | **0.2273** | **0.1370** | ~0.314 | ~0.218 | ~0.558 | **0.2391** |

**Takeaway:** LogReg ≈ XGB (AUPRC 0.2274 vs 0.2273). Not a learner problem. XGB F1-max lift over OOF flag-everything ≈ **1.10×** (0.314 / 0.285).

### E4 served locked-test (published quote only)

Base rate = 233/1788 = **13.0%**. Flag-everything F1 = **0.231**.

| Seed | F1 | P | R | AUPRC | Verdict |
| ---: | ---: | ---: | ---: | ---: | --- |
| 7 | 0.2488 | 0.1421 | 1.0 | 0.1572 | FAIL |
| 42 | 0.2460 | 0.1403 | 1.0 | 0.1648 | FAIL |
| 123 | 0.2467 | 0.1407 | 1.0 | 0.2031 | FAIL |

E4 mean F1 ≈ **0.247** → lift over flag-everything ≈ **1.07×**. Precision wall ~0.14 vs floor 0.25. Threshold picker landed on **R = 1.0** for all seeds (seed 42 thr = 0.15).

---

## 2. OOF PR + feasibility (max P at R≥0.375)

| Seed | max P @ R≥0.375 | vs gate 0.20 | vs floor 0.25 |
| ---: | ---: | --- | --- |
| 42 | **0.2411** | ≥ 0.20 | < 0.25 |
| 7 | **0.2357** | ≥ 0.20 | < 0.25 |
| 123 | **0.2405** | ≥ 0.20 | < 0.25 |
| **mean** | **0.2391** | **clears 0.20** | **misses 0.25** |

Plot: `pr_curve_xgb_s42.png`.

Pre-declared **infeasibility gate (P < 0.20)** is **not** crossed. ~0.24 at R≥0.375 is reachable on OOF — still **below Go floor P≥0.25**, and far above E4 served picker (~0.14 at R=1).

---

## 3. Lift@k (XGB OOF, seed 42; peers similar)

| k | n | Precision | Lift vs prev (0.166) | Recall |
| ---: | ---: | ---: | ---: | ---: |
| 5% | 5657 | 0.285 | **1.72×** | 0.086 |
| 10% | 11315 | 0.273 | **1.64×** | 0.164 |
| 20% | 22630 | 0.248 | **1.49×** | 0.298 |

Head-of-list ranking ~1.5–1.7×; collapses toward base rate as coverage widens.

---

## 4. Calibration (reliability + Brier)

XGB OOF Brier mean = **0.1370**. Reliability (seed 42, first bins):

| Mean p | Empirical pos rate | n |
| ---: | ---: | ---: |
| 0.071 | 0.103 | 25727 |
| 0.145 | 0.153 | 52979 |
| 0.236 | 0.221 | 25642 |

Mild low-bin under-confidence; ordered thereafter. Calibration is not the blocking failure. Plot: `reliability_xgb_s42.png`.

---

## 5. Score histograms by class

- `score_hist_xgb_s42.png` / `score_hist_xgb_s7.png` / `score_hist_xgb_s123.png`
- `score_hist_logreg_s42.png`

Pos/neg score masses overlap heavily; positives only weakly shifted right — matches ~1.1× F1 lift.

---

## 6. Ablation ΔAUPRC + bootstrap 95% CI

Δ = AUPRC(full) − AUPRC(drop-group). Positive ⇒ dropped group contributed.

### Drop-group (primary)

| Group | Seed 42 Δ [CI] | Seed 7 Δ [CI] | Seed 123 Δ [CI] | CI includes 0? |
|---|---|---|---|---|
| **text** | +0.0005 [−0.0003, +0.0013] | +0.0024 [+0.0015, +0.0032] | −0.0002 [−0.0011, +0.0008] | **2/3 yes** (42, 123) |
| **price** | +0.0628 [+0.0594, +0.0661] | +0.0630 [+0.0593, +0.0668] | +0.0608 [+0.0571, +0.0648] | **no** (all) |
| **calendar** | +0.0003 [−0.0013, +0.0018] | −0.0033 [−0.0050, −0.0019] | −0.0039 [−0.0055, −0.0024] | mixed |

**Price carries essentially all OOF lift.** Text (FinBERT scalar) ≈ 0. Calendar/spy ≈ 0 or slightly harmful on some seeds.

### Drop-one (seed 42)

| Feature | ΔAUPRC | CI excl 0? |
|---| ---: | --- |
| volatility_20d | **+0.0164** | yes |
| drawdown_20d | +0.0022 | yes |
| finbert_sentiment | +0.0005 | no |
| return_5d_prior | +0.0003 | no |
| spy_return_5d | +0.0004 | no |
| rs_20d | +0.0001 | no |
| return_20d_prior | ~0 | no |
| volatility_5d | −0.0003 | no |
| spy_volatility_20d | −0.0025 | yes (negative) |

Dominant single feature: **volatility_20d**. FinBERT scalar is noise-level.

---

## 7. FP themes (XGB OOF, seed 42, F1-max thr≈0.164)

n_fp=37701 · n_tp=10467 · n_pred_pos=48168 (P≈0.217, R≈0.557)

### Ticker (top FP count / rate)

| Ticker | FP | n_OOF | FP rate |
|---| ---: | ---: | ---: |
| NFLX | 1631 | 2739 | 0.60 |
| MU | 1485 | 2165 | 0.69 |
| NVDA | 1469 | 2308 | 0.64 |
| M | 1052 | 1679 | 0.63 |
| **TSLA** | 1020 | 1158 | **0.88** |
| CMG | 920 | 1990 | 0.46 |
| QCOM | 859 | 2178 | 0.39 |
| DAL | 751 | 1569 | 0.48 |

High-vol names dominate — consistent with price/vol-driven scores, not headline semantics.

### Regime (spy_return_5d quintiles)

FP rate elevated at both tails (Q1≈0.356 · Q5≈0.357) vs mid (Q4≈0.307). Mild U-shape; not a single-regime failure.

### Headline clusters (TF-IDF MiniBatchKMeans on FPs, k=6)

| Cluster | n | Theme |
| ---: | ---: | --- |
| 1 | 28575 | benzinga / earnings / upgrades / downgrades (wire clutter) |
| 2 | 3339 | shares trading higher/lower |
| 0 | 1902 | vs est / option alert |
| 3 | 1117 | market session / stocks moving |
| others | ~2.8k | mid-day updates / biggest movers / price-target changes |

FP headlines are mostly generic wire / market-wrap / options-alert copy — not a concentrated narrative the FinBERT scalar could have captured.

---

## 8. Pre-declared decision (filled)

### (i) P@R≥0.375 < 0.20 → infeasible → Bet 2

- Mean OOF max P @ R≥0.375 = **0.2391** ≥ 0.20  
- **Triggered: NO**  
- Note: still **below Go floor P≥0.25**; clearing the 0.20 gate ≠ passing floors.

### (ii) Feasible on OOF but picker chose R≈1 → selection-rule defect → fresh holdout + fixed rule

- Feasible region exists on OOF (all seeds max P ≥ 0.20 at R≥0.375).  
- E4 published served recall = **1.0** for seeds 42/7/123 (thr 0.15 on seed 42).  
- OOF F1-max recall is ~0.55–0.57 (F1-max is saner on OOF; defect is val→served transfer of a near-flag-everything threshold).  
- **Triggered: YES** → pre-register a fixed rule (e.g. max-F1 subject to P≥0.25 on inner val) and evaluate **only on a fresh holdout**. Do not re-use the burned served locked test for a new Go.

### (iii) Text-group ΔAUPRC CI includes 0 → Bet 3 eligible

- Seeds 42 & 123: CI includes 0. Seed 7: small positive Δ (+0.0024) CI excludes 0.  
- Majority (2/3) includes 0.  
- **Triggered: YES** → Bet 3 (richer text) is **eligible**, not proven. Run only under the active contract after (ii)/Bet 2 hygiene.

### Primary next step

**Selection-rule fix on a fresh holdout** (decision ii). Bet 2 (label-contract v2) remains the high-EV claim change if Tom wants to reframe −3%/5d; Bet 1 did **not** prove infeasibility under the 0.20 gate, but it did prove (a) learner≈LogReg, (b) signal≈price/vol, (c) text≈0, (d) E4 picker R=1 on served.

---

## Artifacts

| Item | Path |
|---|---|
| This summary | `runs/sample_expand_2026-09-25/wp-bet1/summary.md` |
| Machine-readable | `runs/sample_expand_2026-09-25/wp-bet1/diagnosis.json` |
| Script | `runs/sample_expand_2026-09-25/wp-bet1/diagnose_bet1.py` |
| Log | `runs/sample_expand_2026-09-25/wp-bet1/diagnose.log` |
| OOF scores (s42) | `runs/sample_expand_2026-09-25/wp-bet1/oof_scores_s42.npz` |
| Plots | `pr_curve_xgb_s42.png`, `reliability_xgb_s42.png`, `score_hist_xgb_s{42,7,123}.png`, `score_hist_logreg_s42.png` |

Wall time ≈ **4.0 min** (237.9 s) on M2 Pro · workers=1 · OMP_NUM_THREADS=1.

## STOP / anti-shopping

- No Go claim. Fail stays Fail.  
- No floor change, feature swap, volume add, ticker re-pick, or locked-test re-score.  
- Leave **uncommitted** unless Tom asks.  
- Option-a checkout not used.
