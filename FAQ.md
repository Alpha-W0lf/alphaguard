# AlphaGuard — Technical FAQ

Technical Q&A for the **replay-first** local demo. Contracts SSOT: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Product / why: [`docs/VISION.md`](docs/VISION.md). Finance claims: [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md).

**Status:** The local demo runs end to end on fixtures, and CI runs it on every PR. The Option B path trains the research risk model locally. **License:** PolyForm Noncommercial 1.0.0 — source-available / non-commercial (not OSI open source; not MIT). See [`LICENSE`](LICENSE).

---

## 1. Why only `BUY|HOLD|PASS` — why reject `SELL`?

**AG1** locks v1 Agent 1 actions to `BUY | HOLD | PASS`. `SELL` is unsupported: schema reject / repair prompt — never silently remap. The gate is a downside-risk *regime* check on proposed exposure, not a full long/short trading desk. See ARCHITECTURE §7.2.

## 2. How does the gate map `(action, downside_risk_score)` → approve/reject?

Agent 2’s XGBoost emits `downside_risk_score` (`proba_high_risk`). A **code-owned deterministic policy** then decides:

| Action | Policy |
|--------|--------|
| `BUY` | `reject` if score ≥ `score_threshold` (or optional vol veto); else `approve` |
| `HOLD` / `PASS` | Always `approve` (no directional trade); score still recorded |

Optional vol veto rejects **`BUY` only** and is policy, not part of the learned label. See §7.4 / `tests/test_gate.py`.

## 3. What is the learned label, and why never OR volatility into it?

**AG2:** `label_high_risk = 1` iff forward 5-session return `< -0.03`. Volatility may be a **feature** and/or a **deterministic BUY veto**, but must never be OR’d into the training label. Mixing current vol into the target turns a downside-return model into a blurred risk composite whose score no longer means one thing.

## 4. How does unified as-of prevent look-ahead leakage in RAG hits?

The event clock is UTC `published_at`. Every `RetrievalHit` carries `available_at` and must satisfy `available_at <= published_at` before prompting. Features use only the last **completed** session (`feature_as_of`). Tests fail on a future retrieval hit (`tests/test_asof.py`) and on a same-day close used as a feature (`tests/test_dataset_build.py`). Training splits get the same treatment: the harness tests for leakage across split boundaries, and caught one ([`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) §7).

## 5. Why can `HOLD`/`PASS` approve while `BUY` rejects at the same score?

Same `downside_risk_score` can reject `BUY` (directional exposure) and still approve `HOLD`/`PASS` (no trade). The score is risk context; the **action** changes whether policy treats it as blocking. Do not expect “high score ⇒ always reject.”

## 6. Why must we not cite fixture `train_f1_at_threshold=1.0` as model quality?

`bundle_kind=fixture` is synthetic plumbing (`n_rows=64`). It proves the load/score/policy path. Model metrics come only from a locally trained `bundle_kind=option_b` manifest (`scripts/train_option_b_gate.py`) and the study records in [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md).

## 7. How are experiment results recorded?

Every run records its dataset hash, config hash and git SHA, and is scored against floors fixed before the run. The leakage audit and the purge it led to are in [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) §7, with the audit's run records in `runs/leakage_audit_2026-09-25/`. Shipped defaults stay `train_f1_max` until a person promotes a candidate ([`docs/PROMOTION_POLICY.md`](docs/PROMOTION_POLICY.md)).

## 8. What does replay-first prove vs what Kafka E2E still needs to prove?

Replay proves: fixtures → `PipelineService` → retrieval hits → Agent 1 → gate → **local run summary**, with Kafka **down**. With Docker Compose up, the stack adds produce/consume + idempotent Qdrant upsert + `/trigger`; an optional Yahoo RSS producer (`rss poll`) rounds it out — still **not** production SRE / agent-on-consume.

## 9. What is `replay_fixture` vs `kafka_integration`?

ARCHITECTURE §16 resource modes. Smoke defaults to `resource_mode=replay_fixture` (`ALPHAGUARD_RAG_MODE=fixture`, Kafka optional/down). `kafka_integration` = `ALPHAGUARD_MODE=live` + `ALPHAGUARD_RAG_MODE=qdrant`; `/health` probes Kafka (2s). Do not claim Kafka maturity from fixture smoke alone.

## 10. What happens on old Ollama 412, and what is the documented fallback?

Default `OLLAMA_MODEL=gemma4:e2b` needs a current Ollama (Gemma 4 can **412** on old builds). Upgrade Ollama, or set `OLLAMA_MODEL=qwen3.5:4b` / use `OLLAMA_FALLBACK_MODEL`.

## 11. Who owns `event_id`/`ticker` if the LLM returns different values?

**Application owns identity.** `PipelineService` overwrites `event_id` and `ticker` from the input `NewsEvent` before scoring. LLM mismatches are logged (`identity_mismatch`); we never score the wrong event’s features. See §7.2.

## 12. Are LangSmith/Phoenix “wired,” and what is the real LLMOps baseline?

Local run summary under `artifacts/runs/*.json` is **mandatory and real**. When tracing + an API key are configured, LangSmith emits a real Client run (`ok` only after emit; `extras.langsmith_run_id` on success). When `PHOENIX_ENABLED=true`, Phoenix emits a real OpenInference chain span (`ok` only after emit+flush; `extras.phoenix_span_id` on success). Default smoke has both off → `skipped` (no LangSmith key or Phoenix collector required).

## 13. Why can the same event show `BUY` or `HOLD` across smokes?

Agent 1 is LLM-sampled (stochastic). Agent 2’s **policy table is deterministic** given fixed `(action, score[, vol])`. Variance in proposals is expected; do not chase a golden proposal screenshot.

## 14. Does `docker-compose.yml` prove Kafka delivery contracts?

Compose proves pinned images + operator path: producer/consumer, DLQ, UUID5 upsert, and `/trigger`; plus a thin `rss poll` (Yahoo may flake; fixture XML for CI). Smoke must still succeed with Kafka **stopped** (`Makefile` comment).

## 15. What happens to an out-of-universe ticker or invalid proposal?

Universe is locked (`AAPL`, `MSFT`, …). Out-of-universe tickers are **rejected** in builders/fixtures — no silent remap. Invalid proposals (`SELL`, malformed JSON): schema reject / one repair retry, then fail closed — no fake approve. See §7.1–7.2 and failure-mode table.

## 16. Where do unit tests vs executable goldens carry the invariants?

**Unit tests** (`tests/test_gate.py`, `test_asof.py`, `test_contracts.py`, `test_train_option_b.py`, …) carry hard invariants: gate table, as-of filter, identity overwrite, no `SELL`, train-only HPO/threshold. **Executable goldens** (`eval/golden_cases.jsonl`, ≥21 rows) are parametrized against real façades via `alphaguard.eval` (schema/identity/as-of/gate/OOU, including fixture-path OOU + tmp-manifest vol-veto). The goldens count structural schema ok/reject cases; a live-model analyst eval is the next step (README, Next).

## 17. (Bonus) Is FinBERT in the smoke path?

No. FinBERT is offline batch only. Smoke uses a precomputed fixture sentiment column so 16GB machines are not co-scheduling FinBERT + Compose + Ollama.

## 18. (Bonus) Does Agent 1 `confidence` change the gate?

No. Confidence is validated for schema completeness, then **ignored by policy** — trace / review signal only (§7.4).

---

**Clone path:** [`GETTING_STARTED.md`](GETTING_STARTED.md) · **Pipeline card:** [`docs/assets/`](docs/assets/)
