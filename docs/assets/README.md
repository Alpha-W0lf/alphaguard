# Packaging visuals (AlphaGuard)

| File | What it shows |
|------|----------------|
| [`pipeline_overview.png`](./pipeline_overview.png) | Storefront proof card — News → Context → Trade idea → Risk check (designed; no fake scores) |
| [`smoke_terminal.png`](./smoke_terminal.png) | Optional eng evidence: `make smoke` excerpt (Kafka down; paths redacted) |
| [`run_envelope_curated.png`](./run_envelope_curated.png) | Optional eng evidence: curated local run JSON baseline |

## Captions (binding)

1. **pipeline_overview.png** is the README proof strip — capability framing, not a live trading UI.
2. Local run summary under `artifacts/runs/` remains the mandatory LLMOps baseline when you run smoke.
3. Default smoke: `obs.langsmith=skipped` and `obs.phoenix=skipped` unless configured.
4. Absolute home paths are **redacted** in committed terminal/envelope images.
5. Do not invent LangSmith/Phoenix UI screenshots or PnL claims.

Source for smoke/envelope refresh notes: prior packaging runs under gitignored `artifacts/`. Pipeline card added 2026-07-31 (sales-first README pass).
