<!-- Author: Claude Opus (claude -p --model opus) on Mac 2026-09-25 ~2:40 PM CT; executor: Job Hunt / Grok Bot. PLAN ONLY. Landed by executor after -p Write was permission-denied; bytes recovered from Opus Write tool payload (session 71296b42). -->
---
title: JH-63 Sample/Volume Expand Strategy Plan
date: 2026-09-25
author: Claude Opus via claude -p --model opus on Mac
executor: Job Hunt
status: PLAN ONLY
base_commit: 1f53808d0945bab0b7a3119a9ee00ab524df6145
freeze_option_b: 001856a6 (n=8907)
floors: F1≥0.30 P≥0.25 AUPRC≥0.18
---

# JH-63: Sample/Volume Expand Strategy Plan

**Status:** PLAN ONLY. No code, no training, no config edits in this artifact.
**Model Quality Go:** UNCLAIMED. The Option A clean nested Fail stands and the Option B nested Fail stands. Fail stays Fail.
**Floors (pre-registered, unchanged):** F1 ≥ 0.30, Precision ≥ 0.25, AUPRC ≥ 0.18. All three must clear on every seed.

## 0. Evidence provenance

| Source | How it was read this session | Status |
|---|---|---|
| `runs/optionB_2026-09-25/summary.md`, `wp-b4/summary.md`, `wp-b4/nested/xgb_gain.json`, `wp-b2/build.log` | Opened | Verified |
| `docs/plans/2026-09-25_jh63_option_b_features_freeze_plan.md` | Opened | Verified |
| `docs/EXPERIMENTS.md` §7–§10 (Phase C audit, Go-gate re-run, Phase B purge-on, Option B) | Opened | Verified |
| `docs/TRAINING_DATA.md` | Opened | Verified |
| `scripts/build_training_events.py`, `src/alphaguard/ml/dataset_build.py`, `dataset_ingest.py`, `dataset_asof.py` (fetcher), `src/alphaguard/contracts/events.py` (`TICKER_UNIVERSE`) | Opened | Verified |
| `.cursor/rules/workflow-os-portable.mdc` (in-repo QUALITY_STANDARD summary) | Opened | Verified |
| scikit-learn docs: TimeSeriesSplit, cross-validation guide, learning curve guide, `learning_curve`, `average_precision_score`, model evaluation, PR example, `permutation_test_score`, common pitfalls | Fetched live (scikit-learn 1.9.1) | Verified |
| `second_brain/.../QUALITY_STANDARD.md`, custom_resumes backlog (`2026-09-24_jh63_3_sample_expand_inventory.md`, Phase C labels/data plan, prep inputs, Option A leakage plan, purge-align nested Go) | **Read permission denied** in this session (outside the worktree sandbox) | **Unverified**: diagnosis relies on the in-repo mirrors (EXPERIMENTS.md §7–§10, TRAINING_DATA.md, run summaries), which carry the same numbers |
| López de Prado (AFML, PBO), Saito & Rehmsmeier, Figueroa et al., Google ML Crash Course | Fetch/search **permission denied** for non-sklearn domains this session | **Unverified this session**: cited by title and URL from bibliographic knowledge, paraphrased with no quotes. WP-E0 asks the executor to open each URL and confirm |
| Row-level profile of the freeze parquet (unique ticker-days etc.) | Python read was **blocked** (`data/` resolves into the main checkout) | **Unknown**: WP-E0 measures it |

## 1. Plain-English diagnosis

### 1.1 What n=8907 actually is (Verified)
The 8907 rows are **not** the ceiling of the news archive. They are the ceiling of the **8-ticker universe filter**:

- `wp-b2/build.log`: `ingest: raw=1400469 universe=10215 dedup=8907 sampled=8907 oou_dropped=1387675`.
- The universe filter keeps **10,215 / 1,400,469 = 0.73 %** of the archive. `TICKER_UNIVERSE` = `{AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ}` (`src/alphaguard/contracts/events.py:10`). `load_filter_dedup_sample` drops everything else (`dataset_ingest.py:205-207`).
- `MSFT` and `SPY` have **0 rows** (build log warning; TRAINING_DATA.md coverage table). So the model trains on **6 tickers**.
- Rows by ticker: NVDA 3124, QQQ 2772, GOOGL 1824, AAPL 469, META 389, AMZN 329. **NVDA + QQQ + GOOGL = 7720 / 8907 = 86.7 %.**
- `--target-rows` defaults to 500 (`dataset_build.py:222`). JH-63.3 passed a value ≥ the deduped pool, so `sampled == dedup`. "Full pool" means the full *8-ticker* pool, nothing more.

### 1.2 The effective sample is far smaller than 8907 (Verified inputs, derived bound)
- Every price feature (8 of 9) is a function of `(ticker, feature_as_of)` only (`dataset_asof.compute_features_and_label`). Only `finbert_sentiment` varies between headlines on the same ticker-day, and its XGB gain is **≈0 on all three seeds** (0.00 / 0.00 / 0.53; `wp-b4/nested/xgb_gain.json`).
- Phase C C1 (EXPERIMENTS.md §7) reports **7822 rows** in repeated `(ticker, feature_as_of)` groups. Whichever way that counter is defined, the number of distinct ticker-days is **at most ~5,000** (upper bound if every repeated group has only 2 rows) and possibly close to **~1,100**. The exact number is **Unknown**, and WP-E0 measures it.
- Labels are 5-session forward returns, so consecutive ticker-days share most of their label window. López de Prado calls these *concurrent labels* (AFML Ch. 4). They are not independent draws.
- Positives cluster on market-wide selloffs. Phase C gate (b) shows fold 1 at a QQQ same-day forward median of −3.2 % on 97 % of positives, and the locked test at a QQQ forward median of −9.5 %. Six correlated tech names falling on the same day are closer to **one regime event** than to six samples.
- **Net:** the model effectively learns from a few thousand overlapping ticker-days, dominated by 3 names and a handful of drawdown regimes. That is data starvation in the sense that matters (independent regimes and names), even though the row count looks healthy.

### 1.3 Signal starvation is also real (Verified)
- Locked-test prevalence is **0.1308** (233 / 1782; EXPERIMENTS.md §7, §9). AUPRC for a no-skill classifier equals prevalence (scikit-learn PR example, `plot_chance_level`).
- Option B nested AUPRC / prevalence = **1.01 / 1.03 / 1.17** (seeds 42 / 7 / 123). Those scores are **barely above chance**.
- Option A 534a clean nested = **1.40 / 1.36 / 1.30** (`wp-b4/summary.md` side-by-side). That is weak but real lift, and still below the 0.18 AUPRC floor.
- FinBERT headline sentiment contributes ~0 gain, so the "news" part of the news-risk model currently carries no measurable signal.

### 1.4 Why Option B made things *worse* (Estimated, not proven)
Four more close-derived features on the **same** ~few-thousand ticker-days lowered nested scores on **every** seed (F1 0.25–0.29 → 0.10–0.18). The pattern fits a high-variance regime: more feature degrees of freedom with no more independent data. Trees then split on noise in `rs_20d`, `drawdown_20d` and `volatility_20d`, which dominate gain. The pattern also fits "the new features are anti-informative out of time". Estimated, not proven: WP-E1's learning curve is the instrument that separates these explanations, which is why it comes before any build.

### 1.5 What is and is not starved

| Axis | Status | Evidence |
|---|---|---|
| Rows in current universe | **Exhausted** at 8907 | build log `dedup=8907 sampled=8907` |
| Rows in archive | **Barely used** (0.73 %) | build log `oou_dropped=1387675` |
| Tickers | **Starved**: 6 names, 3 carry 87 % | build log rows_by_ticker |
| Regimes / time | **Starved**: fold 0 positives 99.4 % NVDA (2016–2018 archive only has NVDA and QQQ) | EXPERIMENTS.md §7 gate (b) |
| Volume / OHLCV | **Unused**, but *cheap*: `yf.download` already returns OHLCV and the code keeps only `Close` | `dataset_asof.py:103-116` |
| Label definition | Locked `fwd_return_5d < -0.03`. Tom locked no relabel. | TRAINING_DATA.md, EXPERIMENTS.md §7 WP-C5 |
| Feature family | Close-only price features are saturated (Option B Fail). Text signal ≈0. | xgb_gain.json |
| Leakage / embargo | **Fixed**: trading-day purge, 0 overlap rows | EXPERIMENTS.md §7, §9; PR #19 |

**Conclusion:** the remaining gap is **not** the old embargo bug. It is (a) too few *independent* ticker-regime observations and (b) weak per-row signal. Rows from **more names over the same period** attack (a) directly and are the only cheap lever that does not reuse the same 8907 rows.

## 2. Literature and best-practice brief (what we must not violate)

1. **Time-ordered splits only.** scikit-learn: TimeSeriesSplit exists because other CV methods "would lead to training on future data and evaluating on past data". Its `gap` parameter excludes samples "from the end of each train set before the test set". KFold/ShuffleSplit assume i.i.d. and give "poor estimates of generalization error" on autocorrelated data.
   - *TimeSeriesSplit — scikit-learn 1.9.1*: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html (Verified)
   - *3.1 Cross-validation: evaluating estimator performance*, §Cross-validation of time series data: https://scikit-learn.org/stable/modules/cross_validation.html (Verified)
2. **Group dependence.** The same cross-validation guide (§3.1.2.4) says "the i.i.d. assumption is broken if the underlying generative process yields groups of dependent samples". Validation must come from groups "not represented at all in the paired training fold". For us, **ticker-day (and same-date cross-ticker) rows are groups.** Subsampling and permutation must operate on groups, not rows. (Verified, same URL.)
3. **Purge and embargo; CPCV.** López de Prado's *Advances in Financial Machine Learning* (Wiley, 2018) makes three points:
   - Ch. 7 argues that standard k-fold leaks in finance because labels overlap in time. It prescribes **purging** training observations whose label windows overlap the test window, plus an **embargo** after the test window.
   - Ch. 4 introduces **label concurrency / average uniqueness** and uniqueness-based sample weights.
   - Ch. 12 introduces **Combinatorial Purged CV (CPCV)**, which produces many backtest paths.

   Caveat: CPCV reduces single-path luck but multiplies the number of evaluations. Reading multiple paths as permission to pick the best one is exactly the selection bias quantified in Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*.
   - Book: https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086 (**Unverified this session**, paraphrase only)
   - *The Probability of Backtest Overfitting*: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253 (**Unverified this session**)
   - *The 10 Reasons Most Machine Learning Funds Fail*: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 (**Unverified this session**)

   Our trading-day purge (PR #16/#19) implements the purge idea. CPCV is **not** adopted in this plan (see §7).
4. **No fitting on test.** scikit-learn *Common pitfalls* §12.2 says to split first and "never include test data when using the fit and fit_transform methods".
   - https://scikit-learn.org/stable/common_pitfalls.html (Verified)
   - Applied here: the learning curve and permutation test in WP-E1 run on the **dev block only**. The locked test is untouched until WP-E4.
5. **Rare-event metrics.** scikit-learn says "Precision-Recall is a useful measure of success of prediction when the classes are very imbalanced", and the PR chance level is the positive-class prevalence. `average_precision_score` is the non-interpolated `Σ(Rₙ−Rₙ₋₁)Pₙ`, which differs from trapezoidal PR-AUC, and the docs call trapezoidal "too optimistic". Accuracy can be "above chance only because the classifier takes advantage of an imbalanced test set".
   - https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html (Verified)
   - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html (Verified)
   - https://scikit-learn.org/stable/modules/model_evaluation.html (Verified)
   - Saito & Rehmsmeier, *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets*, PLoS ONE 10(3): e0118432 (2015), https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432 (**Unverified this session**)
   - Google ML Crash Course, *Datasets: Class-imbalanced datasets*, https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets (**Unverified this session**)
   - **Rule:** always report AUPRC **and AUPRC / prevalence** next to the floors.
6. **Learning curves before claiming more data or features help.** scikit-learn §3.5.2 describes two patterns:
   - When training and validation scores "converge to a value that is quite low with increasing size of the training set … we will probably not benefit much from more training data".
   - When "the training score … is much greater than the validation score. Adding more training samples will most likely increase generalization".

   `learning_curve` defaults to `KFold`/`StratifiedKFold` with `shuffle=False`. For time series we must supply our own purged time split and group subsampling.
   - https://scikit-learn.org/stable/modules/learning_curve.html (Verified)
   - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.learning_curve.html (Verified)
   - Figueroa, Zeng-Treitler, Kandula & Ngo, *Predicting sample size required for classification performance*, BMC Med Inform Decis Mak 12:8 (2012), fits inverse-power-law learning curves to extrapolate performance vs n: https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-12-8 (**Unverified this session**)
7. **Is there any signal at all?** `permutation_test_score` tests "the null hypothesis that features and targets are independent". The p-value is `(C+1)/(n_permutations+1)`. A large p-value "may indicate lack of real dependency or that the estimator was unable to use the dependency".
   - Ojala & Garriga, *Permutation Tests for Studying Classifier Performance*, JMLR 11 (2010).
   - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.permutation_test_score.html (Verified)
   - With concurrent labels, permute **labels at the ticker-day group level** so the null is not trivially easy to beat.

## 3. Options ranked (re-ranked with evidence)

Every "lift" entry is **Estimated** or **Unknown**. No percentages are claimed.

| Rank | Option | What changes | Expected lift | Main risks | Effort | Time-to-signal |
|---|---|---|---|---|---|---|
| **1** | **Training-universe expand (same archive, same label, same 9 features, same period)** | Admit more archive tickers into *training* by a pre-registered rule. Serving universe and locked-test population unchanged. | **Estimated positive, if** WP-E1 shows a variance-dominated curve. Attacks the diagnosed starvation (names and independent ticker-days) directly. **Unknown** magnitude. | Survivorship (yfinance lacks many delisted names → rows drop); domain shift (small caps ≠ mega-cap tech); FinBERT compute; cross-sectional dependence on selloff days; must not mutate the serving `TICKER_UNIVERSE` contract | Medium (ingest param + builder run + new freeze + configs) | Days (build time Unknown; E0 measures FinBERT throughput) |
| 2 | Volume / OHLCV features on the current 8907 rows | Add e.g. volume z-score and abnormal volume from the existing `yf.download` result | **Estimated small**. It is still a feature slice on the same starved ticker-days, and Option B showed that adding features there hurt. | Same variance trap as Option B; **this would be a feature chase** | **Low**. Option B's "needs a new fetcher" overstated the cost: `yf.download` already returns OHLCV and `dataset_asof.py:112` keeps only `Close`. Still a new freeze. | Hours–1 day |
| 3 | Event/label expand (denser sampling: all ticker-days, not only headline days; or add `raw_partner_headlines.csv`) | More rows per ticker | **Unknown**. All-ticker-days changes the product question from news-triggered risk to generic drawdown risk and raises label concurrency. The partner-headlines file's coverage of the 6 names is **Unknown** (only SPY=14 is documented). | Silent task change; heavier overlap; relabel is Tom-locked | Low–Medium | Days |
| 4 | Longer history (post-2020) | New news source needed. The archive window ends before `history_end=2021-06-01` (`dataset_asof.py:122`). | **Unknown** | Licensing, new ingest, label/as-of revalidation | High | Weeks |
| 5 | Alternative data (options IV, fundamentals, a different news vendor) | New fetchers + contracts | **Unknown** | Licensing, cost, leakage surface | High | Weeks+ |

**Why volume is not primary despite being cheap:** cheapness was never the objection that matters. It would be a second feature chase on the same ~few-thousand ticker-days, and it violates the lock "no close-only feature chase as primary". It stays **conditional**: if WP-E4 passes with the expanded universe, volume can be a later pre-registered slice. It never runs in parallel with E2–E4, because that would be feature shopping.

## 4. Recommended path (ONE primary)

**Primary:** *Diagnose, then run a training-universe expand.* Measure effective n and the learning curve on freeze `001856a6` first. If and only if the curve says more independent data should help, build a new freeze that adds archive tickers **to training only**. Evaluate on the **same locked-test rows** as `001856a6` with the **same features, label, purge, seeds and floors**.

The key design choice is a **paired comparison**. The served-universe locked-test rows (the 1782 rows, 233 positives) stay byte-identical, so the *only* change is the training population. Any movement is attributable to sample expansion, not to a new test set.

### Prerequisites
- P1. Clean worktree from `main@1f53808`. **Never** the dirty `/Users/tom/Documents/Git/alphaguard` (option-a) checkout.
- P2. `data/` in this worktree resolves into the main checkout (Verified: the `ls data/raw/...` path resolved to `/Users/tom/Documents/Git/alphaguard/data/raw/...`). **Every build must write to a new `--out` path.** Overwriting `data/derived/training_events.parquet` (freeze `001856a6`) is forbidden.
- P3. Tom answers gates G1–G4 (§8) before WP-E2.

### STOP gates (pre-registered)
- **S1 (after E0):** distinct *usable* archive tickers under the E0 rule < 30, **or** projected expanded training ticker-days < 3× current → STOP. The archive cannot deliver meaningful expansion. Return to Tom.
- **S2 (after E1), learning-curve verdict:**
  - *Variance-dominated:* the train–val AUPRC gap at 100 % n is larger than the spread across subsample seeds, **and** val AUPRC is non-decreasing across 25 → 100 %. → Proceed to E2.
  - *Bias-dominated:* the curve is flat within seed spread and the gap is small → **STOP**. More rows of this kind are unlikely to help. Return to Tom with "the feature/label family is the bottleneck".
  - *Ambiguous* → STOP and escalate to Opus. No build.
- **S3 (after E1), permutation test:** group-level permutation p ≥ 0.05 on the dev block → report "no detectable dependency with this feature set". E2 may still proceed only if Tom says so explicitly (G4).
- **S4 (after E2):** the served-universe rows in the new freeze are not identical to `001856a6` (event_id set, features, label) → **STOP** as a builder bug.
- **S5 (after E4):** any seed FAIL → Fail stands. No re-run, no feature swap, no ticker-rule change, no grid change.

## 5. Executable work packages (executor: Grok 4.7 local `agent`)

Common rules for every WP:
- Outputs go to `runs/sample_expand_2026-09-XX/<wp>/summary.md`, and each summary records git SHA, freeze hash and command lines.
- Label every claim Verified, Unverified or Unknown.
- Darwin `--workers 1` with `OMP_NUM_THREADS=1` (`thread_limits.py`).
- Floors unchanged. Seeds nested 42/7/123 and WF 0–4. Purge on (`trading_day_horizon`).
- Model family, hyperparameter grid, threshold method and calibration are **identical** to `configs/studies/jh63_go_gate_nested_purge_001856a6.yaml` and `jh63_wf_expanding4_001856a6.yaml`.
- Anti-shopping: nothing is chosen after seeing a locked-test number.

### WP-E0: Inventory and effective-n audit (read-only; no model fit)
- **Goal:** replace every Unknown in §1 with a number and pre-compute the E2 ticker set by a fixed rule.
- **Inputs:** `data/raw/kaggle_stock_news/*.csv` (all files, including `raw_partner_headlines.csv`), freeze `001856a6` parquet, `dataset_ingest.py` dedup rule.
- **Tasks:**
  1. Freeze profile: distinct `(ticker, feature_as_of)`, distinct `feature_as_of`, positives at ticker-day level, distinct dates with ≥1 positive, positives per ticker per fold. Resolve the Phase C "7822 repeated rows" definition.
  2. Archive profile, post-alias, post-dedup: rows per ticker, date range per ticker, headline-days per ticker, for the whole archive. Separately, coverage of `raw_partner_headlines.csv` for the 6 served tickers.
  3. Apply the **candidate rule** (Tom locks in G2; recommended default):
     - US-listed symbol with ≥ 200 deduped headline rows whose dates fall inside the `001856a6` **dev-block** window.
     - yfinance adjusted closes are available for the whole window (probe via the existing cached fetcher; never the forbidden archive symbols).
     - Rank by headline count and take the top **K = 100** plus the 6 served names.
     - Report the survivorship drop: candidates with no closes (count and list).
  4. FinBERT throughput on 1,000 headlines on this Mac → projected wall time for the E2 build.
  5. Open each **Unverified** URL in §2 and mark it confirmed, or correct the citation in this plan.
- **Artifacts:** `wp-e0/{freeze_profile.json, archive_profile.csv, candidate_tickers.json, survivorship_drop.json, finbert_throughput.json, citations_check.md, summary.md}`.
- **Acceptance:** all numbers reproduced by a committed read-only script (e.g. `scripts/audit_sample_expand.py`, tests for the rule function). `pytest` green with output attached.
- **STOP:** S1.

### WP-E1: Learning curve + permutation test on `001856a6` (dev block only; diagnostic, never a Go input)
- **Goal:** decide between variance-dominated and bias-dominated **before** building anything.
- **Design (pre-registered):**
  - Validation = the last purged fold of the dev block (same boundary as expanding4 fold 3). Training pool = everything before it, purged.
  - Subsample the training pool by **ticker-day group** (all headlines of a ticker-day go together) at fractions {0.25, 0.5, 0.75, 1.0} × subsample seeds {0, 1, 2, 3, 4}. The time range stays fixed, so regime coverage is constant and only n varies.
  - Hyperparameters fixed to the `001856a6` nested winner. No HPO inside the curve.
  - Report train AUPRC, val AUPRC, val AUPRC / val prevalence, and val F1/P at the train-fitted threshold. Mean ± spread per fraction.
  - Permutation test: 200 permutations, labels permuted **within the training pool at ticker-day group level**, scored on the same validation fold (AUPRC). Report the p-value per `(C+1)/(n+1)`.
  - Optional secondary (report only): inverse-power-law fit of val AUPRC vs n, per Figueroa et al. Extrapolation is labelled **Estimated** and is never used as evidence of a pass.
- **Hard rule:** the locked-test rows (index ≥ 7125) are never loaded into this script. Assert it.
- **Artifacts:** `wp-e1/{learning_curve.json, learning_curve.png, permutation.json, summary.md}` with the S2/S3 verdict stated in one line.
- **STOP:** S2 and S3. On STOP, Grok writes the summary and stops. No E2.

### WP-E2: Training-universe ingest + builder (code; one slice)
- **Goal:** build a new freeze with training rows from the E0-locked ticker set. The served universe and serving contract stay untouched.
- **Code:**
  - `dataset_ingest.load_filter_dedup_sample` gains an explicit `training_universe: frozenset[str] | None` (default `None` = `TICKER_UNIVERSE`, byte-identical behavior). `contracts/events.TICKER_UNIVERSE` is **not** edited. Serving validators keep rejecting out-of-universe tickers.
  - The builder CLI gains `--training-universe-file <candidate_tickers.json>`. It writes a `served_universe: bool` column, so the served-universe locked-test slice can be selected by column, not by name heuristics.
  - The locked-test boundary becomes **date-anchored**: the first `feature_as_of` of the `001856a6` locked test, read from its study artifacts. The current 80/20 row fraction would move the boundary in time once rows are added. It is a split-policy option (`split_policy: nested_time_aware_v1_date_anchor`). The old policy stays default and byte-identical.
  - The purge (`trading_day_horizon`) applies across all tickers on the shared XNYS session calendar.
- **Tests:**
  - With `training_universe=None`, output is byte-identical to the current path (hash `001856a6` rebuild check on a fixture).
  - The alias registry still applies, and forbidden price tickers are still rejected.
  - The date-anchored split puts no row with `feature_as_of ≥ anchor` in train.
  - The purge holds across tickers.
  - Serving contract tests are unchanged and green.
- **Build:** FinBERT **on** (`--skip-finbert` forbidden), `--skip-download`, cached close fetcher, `--out data/derived/training_events_jh63e_<NEW8>.parquet`. **Never** the canonical path.
- **Acceptance:**
  - (a) The served-universe rows in the new freeze equal `001856a6` rows exactly: same event_id set and identical 9 features + label.
  - (b) The locked-test served slice = 1782 rows, 233 positives.
  - (c) New `dataset_hash` ≠ `001856a6`, recorded as `<NEW8>`.
  - (d) 0 NaN over the 9 features.
  - (e) rows by ticker, drop counts (no closes / label join), and prevalence of added rows vs served rows are all reported.
  - (f) Full `pytest` green, output attached.
- **STOP:** S4. Any n or prevalence drift on served rows → STOP, Tom.

### WP-E3: Study configs
- Clone the two `001856a6` configs to `jh63_go_gate_nested_purge_<NEW8>.yaml` and `jh63_wf_expanding4_<NEW8>.yaml`. The only diffs allowed: `dataset_path`, `dataset_hash`, `split_policy` (date-anchored) and an `eval_slices: [served_universe, all]` reporting block.
- Grid, floors and seeds are byte-identical. Attach a `diff` of each clone against its source to the summary.
- The `534a` and `001856a6` configs stay untouched as historical record.

### WP-E4: Pre-registered acceptance runs
- **(a) Nested Go, purge-aligned:** seeds 42/7/123, `--workers 1`.
  - **Primary verdict population = served-universe locked-test slice** (same 1782 rows as `001856a6`), subject to G3.
  - Report F1, P, AUPRC, AUPRC/prevalence, n_train, n_train_pos, n_test, n_test_pos and the confusion matrix per seed.
  - A seed passes only if all three floors clear on the primary population.
- **(b) expanding4 WF, purge-on:** seeds 0–4, per-fold + locked-test on both slices. Report only; the verdict comes from (a).
- **(c) Secondary (report only, not a verdict):** full-universe locked-test metrics, per-ticker positives, XGB gain for 9 features per seed, and the cross-split duplicate-headline count (same method as Option B).
- **(d) Side-by-side:** 534a clean nested vs `001856a6` clean nested vs `<NEW8>` clean nested, on the identical served test rows. Every number carries an artifact path.
- **STOP:** S5. Harness `candidate` ≠ Go.

### WP-E5: Summary + living docs
- `runs/sample_expand_2026-09-XX/summary.md`, plus an `EXPERIMENTS.md` §11 entry and a `TRAINING_DATA.md` training-universe section (survivorship caveat included).
- Go **UNCLAIMED** regardless of outcome. Fail results from 534a and `001856a6` remain Fail.

## 6. Honest probability language
- Whether E1 shows a variance-dominated curve: **Unknown**. Option B getting worse with more features is weak evidence *for* variance dominance (**Estimated**), and FinBERT ≈0 gain is evidence that some of the gap is signal, not data (**Estimated**).
- Whether E4 clears all floors on all seeds: **Unknown**. Baseline distance is Verified. On the same test rows, 534a clean nested sits at F1 0.25–0.29, P 0.16–0.19, AUPRC 0.17–0.18. Precision is the farthest floor.
- Whether domain shift from added tickers hurts the served slice: **Unknown**. E4 (c) reports per-population metrics so it is visible either way.
- This plan will not state odds as percentages.

## 7. What NOT to do
- **Floor shopping:** no floor change, no "near-pass", no per-seed cherry-pick, no swapping the verdict population after seeing numbers.
- **Denser grids / HPO expansion:** grid is byte-identical to `001856a6`. No Matrix C expansion.
- **Feature shopping:** no volume, no new windows, no FinBERT swap in this slice. Volume is a *later*, separately pre-registered slice, only after E4.
- **Ticker-rule shopping:** the E0 rule and K are locked by Tom before E2. They are never re-picked after E1 or E4 numbers.
- **Test-population drift:** the served-universe locked-test rows must stay identical (S4). No date-boundary moves.
- **Early Go claims:** harness `candidate` ≠ Model Quality Go. Only Tom locks Go.
- **Freeze without hash discipline:** every new parquet goes to a new path with a recorded hash. No overwrite of `001856a6` or `534a341a`. No builder run into the canonical path (P2).
- **Skipping purge:** no WP runs with purge off. No row-count embargo on multi-ticker frames.
- **CPCV as a rescue:** CPCV is not adopted here. If adopted later, it needs its own pre-registration and a backtest-overfitting control (Bailey et al.). It is never used to find a passing path.
- **Relabel or dedupe:** the label stays `fwd_return_5d < -0.03`. Headline dedupe (the 14 cross-split duplicates) stays Tom's separate call.
- **Dirty checkout:** never share the option-a checkout with Grok.

## 8. Decision gates Tom must lock (yes/no)
- **G1.** Is training on **non-served tickers** acceptable, given that the serving `TICKER_UNIVERSE` contract stays unchanged? (Recommend **yes**. It is the only cheap lever that adds independent data.)
- **G2.** Lock the E0 candidate rule: ≥200 dev-window headline rows, closes available, top **K=100** + the 6 served names. Yes, or give a different K. (Recommend **yes**, locked before E1 runs.)
- **G3.** Is the **primary Go population** the served-universe locked-test slice (the same 1782 rows as `001856a6`), with full-universe metrics secondary? (Recommend **yes**. It keeps the comparison paired and the floors meaningful.)
- **G4.** If E1's permutation p ≥ 0.05 but the learning curve is variance-dominated, may E2 proceed? (Recommend **no**. Park and revisit the feature/label family instead.)
- **G5.** The date-anchored split policy in E2 is a harness change. Approve it as part of this slice? (Recommend **yes**. Without it, adding rows silently moves the locked-test boundary.)

## Executor handoff

```
Order (Grok 4.7 local agent, fresh branch/worktree from main@1f53808; never the option-a checkout):
  WP-E0  read-only inventory + effective-n + candidate rule + citation check  → STOP S1
  WP-E1  learning curve + group permutation on 001856a6 dev block only       → STOP S2/S3
  [Tom locks G1–G5]
  WP-E2  training_universe ingest + date-anchored split + new freeze (--out new path, FinBERT on) → STOP S4
  WP-E3  clone configs (hash/path/split/eval_slices only)
  WP-E4  nested 42/7/123 + WF 0–4, workers=1, purge-on, floors F1≥0.30 P≥0.25 AUPRC≥0.18 → STOP S5
  WP-E5  summary + EXPERIMENTS §11 + TRAINING_DATA; Go UNCLAIMED
Escalate to Opus: ambiguous S2 curve, served-row drift, serving-contract ambiguity, any result outside gate cases.
Leave everything uncommitted until Tom says so.
```
