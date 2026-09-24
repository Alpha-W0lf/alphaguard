# Promotion Policy — AlphaGuard MLOps & Risk Gate

**Audience:** Research engineers, interviewers, and model validators.  
**Scope:** Governance, evaluation stages, and claim boundaries. Propose ≠ Claim.

---

## 1. Executive Summary & Three Distinct Gates

AlphaGuard strictly separates system execution correctness, model statistical validation, and economic utility. These three gates must never be collapsed:

| Gate | What it means | Who claims | Verification |
|------|---------------|------------|--------------|
| **1. Harness Go** | Parallel study runner, registry persistence, compare tables, leakage guards, auto multi-seed promotion *logic*, and isolated bundle artifacts operate without cross-talk or data leakage. | **Engineering (PR + CI)** | Unit & integration tests green; zero test leakage. |
| **2. Model Quality Go (Lab)** | Locked statistical floors on canonical freeze (`534a341a...`): **F1 ≥ 0.30**, **Precision ≥ 0.25**, **AUPRC ≥ 0.18**, on seed 42 **and all required extra seeds** (default: `{7, 123}`) on identical hparams. Zero soft misses permitted. | **Human review only (Tom Chacko)**; harness may only propose `candidate`, never auto-publish Go. | Multi-seed rollup in `study.json` + `compare.md`. Currently **UNCLAIMED**; Fail stays Fail. |
| **3. Economic / Markets Claim (Future)** | Shadow trading vs deterministic rules, transaction costs, execution latency, and market slippage. | **Explicit future ticket; NOT claimed.** | Out of scope for lab tracks. PnL / market claims strictly forbidden by `FINANCE_HONESTY.md`. |

---

## 2. Machine-Checkable Harness Promotion Lifecycle

The automated study harness implements a formal state machine for every experiment study:

```
[ Primary Matrix Discovery ]
             │
             ▼
[ Deterministic Shortlist (top-k=3) ]
             │
             ▼
[ Extra-Seed Evaluation (seeds 7, 123) ]
             │
      ┌──────┴──────────────────────┐
      │                             │
(All seeds pass all floors)    (Any seed fails any floor)
      │                             │
      ▼                             ▼
`promotion_decision: candidate`   `promotion_decision: rejected`
      │
      ▼
(Human Gate: Model Quality Go)
```

### Registry Status Definitions

| Status | Definition | Automated Action |
|--------|------------|------------------|
| `none` | No promotion block defined in study config or multi-seed stage disabled. | Primary matrix results persisted; no extra seed runs triggered. |
| `candidate` | All shortlisted hyperparameters cleared all three locked floors across seed 42 and **all** configured extra seeds (`[7, 123]`). | Logged in parent `study.json` with seed rollup; flags run for human review. Does **not** change shipped defaults. |
| `rejected` | Shortlisted configurations failed one or more floors on either primary seed or required extra seeds. | Logged in parent `study.json` with detailed failure attribution per floor. |

---

## 3. Locked Promotion Defaults & Floor Criteria

The defaults below are locked for the AlphaGuard lab experimentation track:

1. **Shortlist Selection:**
   - `shortlist_top_k = 3`: Up to 3 distinct hyperparameter configurations (deduplicated by seed-agnostic config hash).
   - Deterministic ranking: Primary key `test_f1` (descending) -> `test_precision` (descending) -> `test_auprc` (descending) -> `run_id` (lexicographic).

2. **Extra Seeds:**
   - `extra_seeds = [7, 123]`: Evaluated on the exact same model hyperparameters, threshold fitting method, and calibration policy as the primary seed.

3. **Strict Floor Thresholds (No Soft Misses):**
   - **Test F1 ≥ 0.30**
   - **Test Precision ≥ 0.25**
   - **Test AUPRC ≥ 0.18**
   - A configuration fails if even one seed misses one floor (e.g., $P = 0.2263 < 0.25$ constitutes an immediate rejection).

---

## 4. Leakage and Point-in-Time Discipline

Every evaluation run executed by the harness adheres to point-in-time constraints:
- **Held-out Test Split:** Scored exactly once at the conclusion of training. Test data is never exposed to hyperparameter optimization, threshold fitting, or probability calibration.
- **Inner Fit/Val Splits:** Threshold fitting (`train_f1_max`, `train_val_fbeta_0.5`) and calibrators (`isotonic`, `platt`) fit strictly on train or train-internal validation splits.
- **Dataset Hash:** Verified prior to booster execution. Any discrepancy between expected and computed dataset hash triggers an immediate fail-closed abort.

---

## 5. Model Quality Claim Boundaries

- **Harness Candidate ≠ Model Quality Go:** An automated `candidate` output indicates that multi-seed variance satisfied the minimum stability criteria on held-out test data. It is a necessary prerequisite, not a sufficient condition for deployment.
- **Shipped Default Remains `train_f1_max`:** Until a human reviews multi-seed evidence and explicitly authorizes a model upgrade, the production default remains `train_f1_max`.
- **Honest Fails are Assets:** As established in ticket JH-63.1 and documented in `FINANCE_HONESTY.md`, publishing negative results with root-cause transparency is the core demonstration of engineering integrity.
