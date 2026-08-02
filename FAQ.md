# AlphaGuard — Technical FAQ

Staff-facing Q&A for the **replay-first** local demo. Contracts SSOT: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Product / why: [`docs/VISION.md`](docs/VISION.md). Finance claims: [`docs/FINANCE_HONESTY.md`](docs/FINANCE_HONESTY.md).

**Status:** Bounded local demo is runnable; production hardening and deeper live evaluation are incomplete (finish line = local + CI). Default smoke is still **fixture** — **not** a production risk model. Optional Option B train path is lab metrics only. Yahoo RSS poll may flake. **License:** PolyForm Noncommercial 1.0.0 — source-available / non-commercial (not OSI open source; not MIT). See [`LICENSE`](LICENSE).

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

**AG2:** `label_high_risk = 1` iff forward 5-session return `< -0.03`. Volatility may be a **feature** and/or a **deterministic BUY veto**, but must never be OR’d into the training label. Mixing current vol into the target turns a downside-return model into a mushy risk composite that is hard to defend in interview.

## 4. How does unified as-of prevent look-ahead leakage in RAG hits?

**AG3:** event clock is UTC `published_at`. Every `RetrievalHit` carries `available_at` and must satisfy `available_at <= published_at` before prompting. Features use only the last **completed** session (`feature_as_of`). Future news or same-bar closes cannot enter context/features. Tests in `tests/test_asof.py` hard-fail leaks.

## 5. Why can `HOLD`/`PASS` approve while `BUY` rejects at the same score?

Same `downside_risk_score` can reject `BUY` (directional exposure) and still approve `HOLD`/`PASS` (no trade). The score is risk context; the **action** changes whether policy treats it as blocking. Do not expect “high score ⇒ always reject.”

## 6. Why must we not cite fixture `train_f1_at_threshold=1.0` as model quality?

`bundle_kind=fixture` is synthetic plumbing (`n_rows=64`). Perfect fixture F1 proves the load/score/policy path — **not** Option B generalization. Quote Option B only from a local `bundle_kind=option_b` manifest (`scripts/train_option_b_gate.py`); lab-scale test F1 can be near zero / noisy — still not production proof.

## 7. What does replay-first prove vs what Kafka E2E still needs to prove?

Replay proves: fixtures → `PipelineService` → retrieval hits → Agent 1 → gate → **local run summary**, with Kafka **down**. Guide 04 adds produce/consume + idempotent Qdrant upsert + `/trigger` when Compose is up. Guide 06 adds optional Yahoo RSS → produce (`rss poll`); still **not** production SRE / agent-on-consume.

## 8. What is `replay_fixture` vs `kafka_integration`?

ARCHITECTURE §16 resource modes. Smoke defaults to `resource_mode=replay_fixture` (`ALPHAGUARD_RAG_MODE=fixture`, Kafka optional/down). `kafka_integration` = `ALPHAGUARD_MODE=live` + `ALPHAGUARD_RAG_MODE=qdrant`; `/health` probes Kafka (2s). Do not claim Kafka maturity from fixture smoke alone.

## 9. What happens on old Ollama 412, and what is the documented fallback?

Default `OLLAMA_MODEL=gemma4:e2b` needs a current Ollama (Gemma 4 can **412** on old builds). Upgrade Ollama, or set `OLLAMA_MODEL=qwen3.5:4b` / use `OLLAMA_FALLBACK_MODEL`. Do not claim gemma works without a successful pull/smoke; do not invent a “qwen-only DoD.”

## 10. Who owns `event_id`/`ticker` if the LLM returns different values?

**Application owns identity.** `PipelineService` overwrites `event_id` and `ticker` from the input `NewsEvent` before scoring. LLM mismatches are logged (`identity_mismatch`); we never score the wrong event’s features. See §7.2.

## 11. Are LangSmith/Phoenix “wired,” and what is the real LLMOps baseline?

Local run summary under `artifacts/runs/*.json` is **mandatory and real**. **Guide 07:** when tracing + API key are configured, LangSmith emits a real Client run (`ok` only after emit; `extras.langsmith_run_id` on success). **Guide 08:** when `PHOENIX_ENABLED=true`, Phoenix emits a real OpenInference chain span (`ok` only after emit+flush; `extras.phoenix_span_id` on success). Default smoke has both off → `skipped` (no LangSmith key or Phoenix collector required). Local-envelope screenshots fulfill packaging; do not invent LangSmith/Phoenix UI.

## 12. Why can the same event show `BUY` or `HOLD` across smokes?

Agent 1 is LLM-sampled (stochastic). Agent 2’s **policy table is deterministic** given fixed `(action, score[, vol])`. Variance in proposals is expected; do not chase a golden proposal screenshot. Caption screenshots accordingly.

## 13. Does `docker-compose.yml` prove Kafka delivery contracts?

Compose proves pinned images + operator path. Guide 04 ships producer/consumer, DLQ, UUID5 upsert, and `/trigger`. Guide 06 ships thin `rss poll` (Yahoo may flake; fixture XML for CI). Smoke must still succeed with Kafka **stopped** (`Makefile` comment).

## 14. What happens to an out-of-universe ticker or invalid proposal?

Universe is locked (`AAPL`, `MSFT`, …). Out-of-universe tickers are **rejected** in builders/fixtures — no silent remap. Invalid proposals (`SELL`, malformed JSON): schema reject / one repair retry, then fail closed — no fake approve. See §7.1–7.2 and failure-mode table.

## 15. Where do unit tests vs executable goldens carry the interview invariants today?

**Unit tests** (`tests/test_gate.py`, `test_asof.py`, `test_contracts.py`, `test_train_option_b.py`, …) carry hard invariants: gate table, as-of filter, identity overwrite, no `SELL`, train-only HPO/threshold. **Executable goldens** (`eval/golden_cases.jsonl`, ≥21 rows) are parametrized against real façades via `alphaguard.eval` (schema/identity/as-of/gate/OOU, including fixture-path OOU + tmp-manifest vol-veto). Structural schema ok/reject counts are **not** live-Ollama numeric schema-pass rates — those stay deferred. Still not eval-complete / not production Option B.

## 16. (Bonus) Is FinBERT in the smoke path?

No. FinBERT is offline batch only. Smoke uses a precomputed fixture sentiment column so 16GB machines are not co-scheduling FinBERT + Compose + Ollama.

## 17. (Bonus) Does Agent 1 `confidence` change the gate?

No. Confidence is validated for schema completeness, then **ignored by policy** — trace / interview signal only (§7.4).

---

**Clone path:** [`GETTING_STARTED.md`](GETTING_STARTED.md) · **Screenshots:** [`docs/assets/`](docs/assets/)
