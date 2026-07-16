# Training data — Option B dataset builder (Guide 05a)

**Status:** Builder code landed 2026-07-16. **XGBoost train (Guide 05b) not started.**  
**Fixture gate ≠ Option B evidence.**

## Source (locked)

| Field | Value |
|-------|--------|
| Kaggle id | `miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests` |
| Page | https://www.kaggle.com/datasets/miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests |
| Logical columns | `date`, `stock`, `headline` (`stock` → `ticker`) |
| Universe | `AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ` |
| Output | `data/derived/training_events.parquet` (gitignored) |
| Raw cache | `data/raw/kaggle_stock_news/` (gitignored) |

### License (exact string from Kaggle — operator paste)

Implement could **not** retrieve the Kaggle sidebar License field in this environment (no `kaggle` CLI credentials; outbound HTTPS to kaggle.com blocked by proxy).

**Human action required:** open the dataset page, copy the **License** field exactly, and replace this placeholder:

```text
LICENSE_STRING_PENDING_HUMAN_PASTE_FROM_KAGGLE_SIDEBAR
```

Do **not** commit the raw Kaggle dump. Prefer regenerate locally.

## Regenerate

```bash
# 1) Kaggle API token → ~/.kaggle/kaggle.json
# 2) Optional: uv sync --extra train   # installs kaggle CLI package
uv sync

# Download + unzip (or place an offline unzip under data/raw/kaggle_stock_news/)
kaggle datasets download \
  -d miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests \
  -p data/raw/kaggle_stock_news --unzip

# Prefer Compose Kafka/Qdrant/Ollama down during FinBERT (resource_mode=finbert_train)
uv run python scripts/build_training_events.py

# Shortfall after filters/joins (document why):
uv run python scripts/build_training_events.py --allow-shortfall
```

Discovered CSV filename is printed as `csv_discovered=...` on first successful run — paste that path here after your first download:

```text
CSV_FILENAME_PENDING_FIRST_SUCCESSFUL_DOWNLOAD
```

## As-of / dedup / label policy (binding)

| Rule | Behavior |
|------|----------|
| Date-only `published_at` | America/New_York calendar date @ **09:30 ET** → UTC |
| `feature_as_of` | Last **fully completed** NYSE session (`exchange_calendars` **XNYS**) at/before `published_at` |
| Prices | yfinance **auto_adjust=True** closes |
| Dedup | `(ticker, calendar_date, normalized_headline)` keep first |
| Sample | ≈500 stratified; `random_seed=42` |
| Label | `label_high_risk = 1` iff `fwd_return_5d < -0.03` |
| FinBERT | `ProsusAI/finbert-tone`; score = `P(pos) - P(neg)`; offline batch only |
| Split preview | Time-ordered 80/20 counts printed — **does not train** |

## Builder layout

| Path | Role |
|------|------|
| `scripts/build_training_events.py` | Thin CLI |
| `src/alphaguard/ml/dataset_build.py` | Orchestration |
| `src/alphaguard/ml/dataset_ingest.py` | CSV discover / filter / dedup / sample |
| `src/alphaguard/ml/dataset_asof.py` | Calendar + yfinance features/labels |
| `src/alphaguard/ml/dataset_finbert.py` | Offline FinBERT |
| `src/alphaguard/ml/features.py` | **Fixture-only** — must stay FinBERT-free |

## Honesty

- Dataset builder ≠ Option B model trained.
- Smoke / default pytest must not load FinBERT weights.
- Do not claim v1 complete from this guide.
