# Packaging screenshots (guide 02)

Local-envelope evidence for the replay-first vertical slice. **Not** LangSmith/Phoenix UI.

| File | What it shows |
|------|----------------|
| [`smoke_terminal.png`](./smoke_terminal.png) | `make smoke` excerpt (Kafka down): success, proposal, gate decision, envelope path hint |
| [`run_envelope_curated.png`](./run_envelope_curated.png) | Curated run JSON: `status=success`, `rag_mode=fixture`, `resource_mode=replay_fixture`, honest `obs.langsmith` / `obs.phoenix` stubs |

## Captions (binding honesty)

1. **Local run summary** under `artifacts/runs/` is the **mandatory** LLMOps baseline.
2. Envelope `obs.langsmith` / `obs.phoenix` are **status stubs** (here: `skipped`) — not real SDK spans. Do not invent LangSmith/Phoenix UI screenshots.
3. Agent 1 proposal may vary (`BUY` vs `HOLD`/`PASS`) across smokes; the **gate policy is deterministic** given fixed `(action, score[, vol])`.
4. Absolute home paths (`/Users/...`) are **redacted** in committed images; prefer `artifacts/runs/<id>.json`.

Source run for these assets: `e411e604-425d-4c02-8e57-740c30e251f0` (2026-07-13 Implement pass 22). Raw `artifacts/` stays gitignored.
