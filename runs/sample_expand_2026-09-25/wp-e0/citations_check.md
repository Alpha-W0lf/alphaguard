# WP-E0 citation check — Unverified URLs from sample-expand plan §2

**Date:** 2026-09-25 ~3:10 PM CT  
**Executor:** Grok Bot on Mac `75e939cd-aeeb-4f71-9e40-ae8dfbd16e8c`  
**Worktree:** `/Users/tom/Documents/Git/alphaguard-wt-option-b` @ `main` `1f53808`

| Citation | URL | Result | Notes |
|---|---|---|---|
| López de Prado, *Advances in Financial Machine Learning* (Wiley, 2018) | https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086 | **Confirmed** | Live Wiley product page; ISBN 978-1-119-48208-6; author Marcos López de Prado; Feb 2018. Plan paraphrase (purge/embargo, concurrency, CPCV, PBO caution) not re-verified from book text. |
| Bailey et al., *The Probability of Backtest Overfitting* | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253 | **Partially confirmed** | curl → HTTP 403 Cloudflare challenge (`Just a moment...`). Abstract id 2326253 is the standard SSRN handle for this paper; full page body not readable from this agent. |
| López de Prado, *The 10 Reasons Most Machine Learning Funds Fail* | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 | **Partially confirmed** | Same Cloudflare 403. Abstract id 3104816 is the standard SSRN handle; body unread. |
| Saito & Rehmsmeier, PLoS ONE 10(3): e0118432 (2015) | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432 | **Confirmed** | Live article; title matches; DOI 10.1371/journal.pone.0118432; argues PR plots more informative than ROC under imbalance. |
| Google ML Crash Course — class-imbalanced datasets | https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets | **Confirmed** | Live page; covers majority/minority class, why accuracy is poor, downsampling+upweighting. |
| Figueroa et al., BMC Med Inform Decis Mak 12:8 (2012) | https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-12-8 | **Confirmed** | Live article; inverse-power-law learning-curve fit for sample-size prediction. |
| scikit-learn TimeSeriesSplit | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html | **Confirmed** | sklearn 1.9.1 docs; documents future/past leakage risk and `gap`. |
| scikit-learn cross_validation (time series §) | https://scikit-learn.org/stable/modules/cross_validation.html | **Confirmed** | HTTP 200; title “3.1. Cross-validation…”. |
| scikit-learn common pitfalls | https://scikit-learn.org/stable/common_pitfalls.html | **Confirmed** | HTTP 200; “12. Common pitfalls…”. |
| scikit-learn learning_curve guide | https://scikit-learn.org/stable/modules/learning_curve.html | **Confirmed** | HTTP 200. |
| scikit-learn `learning_curve` API | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.learning_curve.html | **Confirmed** | HTTP 200. |
| scikit-learn `permutation_test_score` | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.permutation_test_score.html | **Confirmed** | HTTP 200. |
| scikit-learn PR example | https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html | **Confirmed** | HTTP 200. |
| scikit-learn `average_precision_score` | https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html | **Confirmed** | HTTP 200. |
| scikit-learn model_evaluation | https://scikit-learn.org/stable/modules/model_evaluation.html | **Confirmed** | HTTP 200. |

## Also opened (plan §0 Unverified local docs)

| Source | Path | Result |
|---|---|---|
| QUALITY_STANDARD.md | `/Users/tom/Documents/Git/second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md` | **Confirmed readable** — senior/staff bar, Verified/Unverified/Unknown honesty, one-slice, Fail stays Fail. In-repo portable mirror: `.cursor/rules/workflow-os-portable.mdc`. |
| JH-63.3 sample expand inventory | `/Users/tom/Documents/Git/custom_resumes/docs/backlog/2026-09-24_jh63_3_sample_expand_inventory.md` | **Confirmed readable** — historical n=500 inventory; superseded by freeze `001856a6` numbers in this WP. |
| Strategy plan SSOT | `custom_resumes/docs/backlog/2026-09-25_jh63_sample_expand_strategy_plan.md` + worktree `docs/plans/` copy | **Confirmed readable**. |

## Citation corrections

No URL corrections required. SSRN bodies remain behind Cloudflare from this agent; treat plan’s bibliographic paraphrase as **still Unverified at quotation level**, with handles confirmed.
