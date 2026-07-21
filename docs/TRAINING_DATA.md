# Training data — Option B dataset builder (Guide 05a)

**Status:** **Review shippable (2026-07-17)** — parquet (05a) + Option B train (05b) verified and Review-complete. Soft pin FinBERT = **`ProsusAI/finbert`**. Preferred CSV `analyst_ratings_processed.csv`. Output `data/derived/training_events.parquet` (gitignored). Default smoke still **fixture**.  
**Fixture gate ≠ Option B evidence** — use `MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b` for Option B demos.  
**Archive aliases (2026-07-21):** coded Soft Adjust registry `fb_meta_v1` (`FB`→`META`) + `goog_googl_v1` (`GOOG`→`GOOGL`); `builder_version=0.1.1`; default **on** (`apply_archive_aliases=True`); prices fetch **META/GOOGL only** (never Yahoo `FB`/`GOOG`).

### Live e2e evidence (2026-07-21 alias rebuild)

| Check | Result |
|-------|--------|
| Ingest | raw=1,400,469 → universe=10,215 → dedup=8,907 → sample=500 |
| Aliases applied | `FB→META=389`, `GOOG→GOOGL=1209` (`fb_meta_v1+goog_googl_v1`) |
| CSV | `data/raw/kaggle_stock_news/analyst_ratings_processed.csv` |
| Parquet rows | **500**; unique `event_id`; `builder_version=0.1.1` |
| Tickers in parquet | `AAPL, AMZN, GOOGL, META, NVDA, QQQ` (MSFT/SPY still absent) |
| Rows by ticker | AAPL 67 · AMZN 67 · GOOGL 86 · META 71 · NVDA 100 · QQQ 109 |
| FinBERT | `ProsusAI/finbert`; scores in ≈[-0.97, 0.93]; no NaN |
| Label rate | ≈0.154 (`label_high_risk`) |
| Split preview | train=400 / test=100 (counts only; **no train** in builder) |
| Tests | `uv run pytest -q` → 109 passed |

### Prior live e2e (2026-07-16, pre-alias)

| Check | Result |
|-------|--------|
| Ingest | raw=1,400,469 → universe=8,617 → dedup=8,278 → sample=500 |
| Tickers in parquet | `AAPL, AMZN, GOOGL, NVDA, QQQ` (META absent — FB OOU before alias) |

### Universe coverage honesty (preferred CSV + archive scan)

Raw `stock` counts in `analyst_ratings_processed.csv` for locked universe symbols:

| Symbol | Rows | Note |
|--------|------|------|
| AAPL | 469 | present |
| AMZN | 330 | present |
| GOOGL | 1585 native + **1209** via `goog_googl_v1` from `GOOG` | coded alias (2026-07-21) |
| NVDA | 3133 | present |
| QQQ | 3100 | present |
| META | **0** native; **389** via `fb_meta_v1` from `FB` | archive `FB` → training `META`; prices = **META only** |
| MSFT | **0** | absent from preferred CSV **and** `raw_analyst_ratings.csv` |
| SPY | **0** | absent from preferred CSV; only 14 rows in `raw_partner_headlines.csv` |

Cross-check (2026-07-16 evidence; reconfirmed 2026-07-21 join probe):

| Probe | Result |
|-------|--------|
| Yahoo `FB` download (2020) | **Fails** — “possibly delisted” |
| Yahoo `FB` quote identity today | Resolves to **ProShares S&P 500 Dynamic Buffer ETF** — **not** Facebook/Meta |
| Yahoo `META` (2020-02→06) | **103** adjusted daily closes; covers FB headline window |
| Yahoo `META` (2013) | Present (Facebook-era continuous series under META) |
| Yahoo `META` (2011 pre-IPO) | Empty (expected) |
| Local FB headlines | 389 rows; 86 unique ET calendar days; **77/86** have same-day META close (rest are non-sessions — as-of join already drops/shifts via XNYS) |
| Join probe (2026-07-21) | `./scripts/run_direct_network.sh uv run python scripts/probe_fb_meta_join.py` → `fb_days=86 meta_same_day_closes=77 coverage=0.8953` — **never downloads FB** |

**Alias pricing rule (soft-pinned / coded 2026-07-21):** versioned registry in `dataset_ingest.py` — `fb_meta_v1` maps archive `stock=FB` → training `ticker=META`; `goog_googl_v1` maps `GOOG` → `GOOGL`. Fetch closes as **`META` / `GOOGL` only**. Hard-reject Yahoo `FB`/`GOOG` on the builder price path. `source_row_hash` fingerprints raw archive `stock`; `event_id` uses post-alias universe ticker. Toggle `apply_archive_aliases=False` for honesty tests. Fail closed if required closes missing (existing builder all-drop + alias-aware message).

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

## Train Option B gate (Guide 05b)

```bash
# Requires data/derived/training_events.parquet (05a)
uv run python scripts/train_option_b_gate.py
# → data/derived/model_bundle_option_b/ (gitignored)
# → artifacts/runs/option_b_train_<utc>.json

# Optional Option B smoke (default smoke stays fixture):
MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b \
ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b \
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke
```

| Pin | Value |
|-----|--------|
| HPO | Train-only `TimeSeriesSplit(n_splits=3)` grid; select by mean val logloss |
| Threshold | Train-F1 max on full-train probs |
| `bundle_kind` | `option_b` |
| Library | `src/alphaguard/ml/train_option_b.py` (+ `train_hpo.py` / `train_eval.py`) |

**Honesty:** Lab-scale test F1 on n_test≈100 is noisy; large train/test F1 gap emits a warning. Not a production risk model. Local manifest after 2026-07-21 alias rebuild: train F1 ≈0.693, **test F1 ≈0.087** (n_positive_test=3) — weak/noisy holdout, not hidden. See [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md).

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
| `scripts/train_option_b_gate.py` | Guide 05b train CLI |
| `src/alphaguard/ml/train_option_b.py` | Option B train orchestration |
| `src/alphaguard/ml/train_hpo.py` | Nested time-grid HPO |
| `src/alphaguard/ml/train_eval.py` | Threshold + PRF1 helpers |

## Honesty

- Dataset builder ≠ production risk model.
- Option B bundle proves **lab train path** (HPO audit + metrics) — default smoke still fixture.
- Smoke / default pytest must not load FinBERT weights.
- Bounded MV build complete ≠ production hardening / deeper live eval complete — do not claim those from 05a/05b alone. See [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md).
