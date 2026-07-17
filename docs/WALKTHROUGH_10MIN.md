# AlphaGuard — 10-minute architecture walkthrough (outline)

**Purpose:** Spoken rehearsal script for the VISION MV walkthrough box.  
**Not v1 Done.** Default smoke = fixture; Option B = lab train path only.

Use this as a prompt card. Practice **aloud without opening the repo**. Check the VISION box only when you can do it cold.

## Minute 0–1 — What it is

- Public **interview lab**: one headline → replay ingest → RAG hits → LangGraph Agent 1 (`BUY|HOLD|PASS`) → XGBoost downside gate → **local** run summary.
- Vertical slice, **not** a trading system / not Lowd Capital.

## Minute 1–3 — Critical path

1. Replay fixtures (Kafka optional for smoke).  
2. `PipelineService` owns orchestration.  
3. RAG returns as-of-filtered hits (`available_at <= published_at`).  
4. Agent 1 proposes action; identity stamped from event.  
5. Agent 2 scores `proba_high_risk`; deterministic policy approve/reject.  
6. Always write local envelope; LangSmith/Phoenix = status stubs today.

## Minute 3–5 — AG1 / AG2 / AG3 (say these)

- **AG1:** Actions `BUY|HOLD|PASS` only — `SELL` reject.  
- **AG2:** Label = forward downside return only — never OR volatility into the label.  
- **AG3:** Unified as-of UTC; features carry `feature_as_of`; no future hits.

## Minute 5–7 — Gate honesty

- Fixture bundle (`bundle_kind=fixture`) ≠ Option B proof.  
- Option B: train CLI + `bundle_kind=option_b` locally; nested time-HPO; train-only threshold; lab test F1 can be noisy/near zero.  
- Default smoke stays fixture unless `MODEL_BUNDLE_DIR` points at Option B.

## Minute 7–9 — Ops / failure modes

- Replay-first; Compose Kafka+Qdrant for thin E2E; Guide 06 thin `rss poll` (Yahoo may flake) — not 24/7 SRE.  
- Ollama default `gemma4:e2b`, fallback `qwen3.5:4b` on old builds.  
- Eval: ≥21 goldens structural — not live-Ollama schema-pass rates.

## Minute 9–10 — What you would build next (honest)

- Packaging/walkthrough polish or agent-on-consume — not “flip smoke to Option B by default.”  
- Stop before overclaiming production risk model.

## Self-check

Can you explain AG2 without looking? Can you say why fixture F1=1.0 is theater? If yes, rehearse twice more, then tick the VISION walkthrough box yourself.
