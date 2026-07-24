# Packaging screenshots (guide 02)

Local-envelope evidence for the replay-first vertical slice. **Not** LangSmith/Phoenix UI.

| File | What it shows |
|------|----------------|
| [`smoke_terminal.png`](./smoke_terminal.png) | `make smoke` excerpt (Kafka down): success, proposal, gate decision, envelope path hint |
| [`run_envelope_curated.png`](./run_envelope_curated.png) | Curated run JSON: `status=success`, `rag_mode=fixture`, `resource_mode=replay_fixture`, honest `obs.langsmith` / `obs.phoenix` as `skipped` (default env) |

## Captions (binding honesty)

1. **Local run summary** under `artifacts/runs/` is the **mandatory** LLMOps baseline.
2. Default smoke: `obs.langsmith=skipped` and `obs.phoenix=skipped`. Guide 07 emits real LangSmith Client runs only when tracing+key are set. Guide 08 emits a real Phoenix/OTEL chain span only when `PHOENIX_ENABLED=true`. Do not invent LangSmith/Phoenix UI screenshots.
3. Agent 1 proposal may vary (`BUY` vs `HOLD`/`PASS`) across smokes; the **gate policy is deterministic** given fixed `(action, score[, vol])`.
4. Absolute home paths (`/Users/...`) are **redacted** in committed images; prefer `artifacts/runs/<id>.json`.

Source run for these assets: `e411e604-425d-4c02-8e57-740c30e251f0` (2026-07-13 Implement pass 22). Raw `artifacts/` stays gitignored.

**Provenance honesty (Align 2026-07-23):** these images prove **fixture replay / local-envelope** packaging. They are **not** fresh proof of later Option B train, RSS poll, or configured LangSmith/Phoenix runs. Refresh only from a real current default smoke after deps are installed; do not invent cloud-observability screenshots.
