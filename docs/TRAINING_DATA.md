# Training data — Option B dataset builder (Guide 05a)

**Status:** Builder + live e2e parquet landed 2026-07-16. Soft pin FinBERT = **`ProsusAI/finbert`**. Preferred CSV `analyst_ratings_processed.csv`. Output `data/derived/training_events.parquet` (gitignored; regenerate locally). **XGBoost train (Guide 05b) not started.**  
**Fixture gate ≠ Option B evidence.**

### Live e2e evidence (2026-07-16)

| Check | Result |
|-------|--------|
| Ingest | raw=1,400,469 → universe=8,617 → dedup=8,278 → sample=500 |
| CSV | `data/raw/kaggle_stock_news/analyst_ratings_processed.csv` |
| Parquet rows | **500**; unique `event_id`; all §7.5 + provenance columns |
| Tickers in parquet | `AAPL, AMZN, GOOGL, NVDA, QQQ` (see universe note below) |
| FinBERT | `ProsusAI/finbert`; scores in ≈[-0.97, 0.94]; no NaN |
| Split preview | train=400 / test=100 (counts only; **no train**) |
| Tests | `uv run pytest -q` → 65 passed |

### Universe coverage honesty (preferred CSV)

Raw `stock` counts in `analyst_ratings_processed.csv` for locked universe symbols:

| Symbol | Rows | Note |
|--------|------|------|
| AAPL | 469 | present |
| AMZN | 330 | present |
| GOOGL | 1585 | present (`GOOG` also exists: 1209 — not remapped) |
| NVDA | 3133 | present |
| QQQ | 3100 | present |
| META | **0** | archive uses **`FB`** (389) — soft pin forbids silent remap |
| MSFT | **0** | absent from this preferred CSV |
| SPY | **0** | absent from this preferred CSV |

Stratified sample + refill therefore concentrates on the five present tickers. **Do not** invent FB→META without a new human soft-pin.

## Source (locked)

| Field | Value |
|-------|--------|
| Kaggle id | `miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests` |
| Page | https://www.kaggle.com/datasets/miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests |
| Preferred CSV | **`analyst_ratings_processed.csv`** (minute timestamps; Kaggle data card) |
| Logical columns | `date`, `stock`, `headline` (aliases: `title` / `article title` → headline; `stock` → `ticker`) |
| Universe | `AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ` |
| Output | `data/derived/training_events.parquet` (gitignored) |
| Raw cache | `data/raw/kaggle_stock_news/` (gitignored) |

### License (exact from Kaggle Data Card, 2026-07-16)

```text
CC0: Public Domain
```

Kaggle also links the license as **CC0: Public Domain**. Acknowledgements on the card note articles remain Benzinga property as scraped content — do **not** commit the raw dump; regenerate locally.

## Network note (Cursor agent / sandbox)

Cursor agent shells often inject `HTTP(S)_PROXY=http://127.0.0.1:…` which returns **403 on CONNECT**, so Kaggle/yfinance/PyPI appear “blocked.” Fix for local Terminal / agent with full permissions:

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy \
  GIT_HTTP_PROXY GIT_HTTPS_PROXY SOCKS_PROXY SOCKS5_PROXY
export NO_PROXY='*'
# then run builder
```

Or use: `./scripts/run_direct_network.sh uv run python scripts/build_training_events.py`

## Regenerate

```bash
# 1) Create Kaggle API token: https://www.kaggle.com/settings → API → Create New Token
#    Place at ~/.kaggle/kaggle.json (chmod 600). Accept dataset rules if prompted.
# 2) Install CLI (lightweight):
uv pip install kaggle
# or: pip install kaggle

uv sync

./scripts/run_direct_network.sh kaggle datasets download \
  -d miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests \
  -p data/raw/kaggle_stock_news --unzip

# Prefer Compose Kafka/Qdrant/Ollama down during FinBERT (resource_mode=finbert_train)
./scripts/run_direct_network.sh uv run python scripts/build_training_events.py
```

Discovered CSV is printed as `csv_discovered=...` (expect `analyst_ratings_processed.csv`).

## As-of / dedup / label policy (binding)

| Rule | Behavior |
|------|----------|
| Minute timestamps | Preserve Eastern wall time → UTC (`published_at_parsed`) |
| Date-only `published_at` | America/New_York @ **09:30 ET** → UTC (soft pin for date-only rows) |
| `feature_as_of` | Last **fully completed** NYSE session (`exchange_calendars` **XNYS**) at/before `published_at` |
| Prices | yfinance **auto_adjust=True** closes |
| Dedup | `(ticker, calendar_date, normalized_headline)` keep first |
| Sample | ≈500 stratified; `random_seed=42`; **unique `event_id` required** |
| Label | `label_high_risk = 1` iff `fwd_return_5d < -0.03` |
| FinBERT | `ProsusAI/finbert`; score = `P(pos) - P(neg)`; offline batch only |
| `--skip-finbert` | **Forbidden** for canonical `training_events.parquet` |
| Split preview | Time-ordered 80/20 counts printed — **does not train** |

## Builder layout

| Path | Role |
|------|------|
| `scripts/build_training_events.py` | Thin CLI |
| `scripts/run_direct_network.sh` | Unset Cursor proxy; run command |
| `src/alphaguard/ml/dataset_build.py` | Orchestration |
| `src/alphaguard/ml/dataset_ingest.py` | CSV discover / filter / dedup / sample |
| `src/alphaguard/ml/dataset_asof.py` | Calendar + yfinance features/labels |
| `src/alphaguard/ml/dataset_finbert.py` | Offline FinBERT |
| `src/alphaguard/ml/features.py` | **Fixture-only** — must stay FinBERT-free |

## Honesty

- Dataset builder ≠ Option B model trained.
- Smoke / default pytest must not load FinBERT weights.
- Do not claim v1 complete from this guide.
- **05b XGBoost train stays parked** until e2e parquet exists and Review says ready.
