# Training data — Option B dataset builder

**Status:** The dataset builder and the Option B training path run end to end. FinBERT = **`ProsusAI/finbert`**. Preferred CSV `analyst_ratings_processed.csv`. Output `data/derived/training_events.parquet` (gitignored). Default smoke still **fixture**.  
**Fixture gate ≠ Option B evidence** — use `MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b` for Option B demos.  
**Archive aliases (2026-07-21):** coded alias registry `fb_meta_v1` (`FB`→`META`) + `goog_googl_v1` (`GOOG`→`GOOGL`); `builder_version=0.1.1`; default **on** (`apply_archive_aliases=True`); prices fetch **META/GOOGL only** (never Yahoo `FB`/`GOOG`).

> **Note:** ML regenerate notes for Option B — **not** required for the stranger clone / `make smoke` path.

### Data at a glance

| Check | Result |
|-------|--------|
| Ingest | raw=1,400,469 headlines → in-universe → **8,907** deduplicated events |
| Aliases applied | `FB→META`, `GOOG→GOOGL` (`fb_meta_v1+goog_googl_v1`) |
| CSV | `data/raw/kaggle_stock_news/analyst_ratings_processed.csv` |
| Tickers with rows | `AAPL, AMZN, GOOGL, META, NVDA, QQQ` (the preferred archive file has no MSFT or SPY headlines) |
| Full-pool freeze | 8,907 events (train 7,125, 7,029 after the purge / locked test 1,782) |
| FinBERT | `ProsusAI/finbert`; score = `P(pos) - P(neg)`; no NaN |

### Universe coverage (preferred CSV + archive scan)

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

## Network note (proxies)

If your shell sets `HTTP(S)_PROXY` to a local proxy that returns **403 on CONNECT**, Kaggle, yfinance and PyPI look blocked. Unset the proxies and run the builder:

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

uv sync --extra train

./scripts/run_direct_network.sh kaggle datasets download \
  -d miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests \
  -p data/raw/kaggle_stock_news --unzip

# Prefer Compose Kafka/Qdrant/Ollama down during FinBERT (resource_mode=finbert_train)
./scripts/run_direct_network.sh uv run python scripts/build_training_events.py --target-rows 8907
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
| Sample | Canonical freeze = the full deduplicated pool (8,907 events; pass `--target-rows` ≥ the pool). The builder default `--target-rows 500` draws a stratified sample (`random_seed=42`). **Unique `event_id` required** |
| Label | `label_high_risk = 1` iff `fwd_return_5d < -0.03` (fraction). `-0.03` itself is `0` |
| Label anchor | First completed XNYS session close at or after the event, through the close **5 trading sessions** later. Weekends and holidays are not sessions |
| Label units | Fraction `close_end / close_start - 1`, not percent |
| Corporate actions | yfinance `auto_adjust=True` (splits and dividends in the close) |
| Halts / delistings | Missing close drops the row. No imputed return |
| As-of | Stored `feature_as_of` is the last completed session whose close is `<= published_at`. FinBERT has no separate clock; the headline is available at `published_at` |
| Embargo | When `feature_as_of` is present, the walk-forward train prefix and the locked-test train prefix stop before the next block's feature session (`embargo_source=trading_day_horizon`), so no training label window reaches into the next block or the locked test. The train-internal validation slice and the 80/20 cut in the single-run trainer (`scripts/train_option_b_gate.py`) are not purged. Without session dates, walk-forward folds keep a 5-row gap (the default) and the locked-test split is a plain 80/20 cut |
| FinBERT | `ProsusAI/finbert`; score = `P(pos) - P(neg)`; offline batch only |
| `--skip-finbert` | **Forbidden** for canonical `training_events.parquet` |
| Split preview | Time-ordered 80/20 counts printed — **does not train** |

### Option B feature set (freeze rebuild 2026-09-25)

Five original features plus four added features. All price features use closes inside the existing `prior20 → feature_as_of` window so n stays 8907.

| Feature | Definition (as-of `feature_as_of`) |
|---|---|
| `finbert_sentiment` | `P(pos) − P(neg)` from `ProsusAI/finbert` on the headline |
| `volatility_20d` | Annualized std of the 20 daily returns ending at as-of |
| `return_5d_prior` | `close(as_of)/close(prior5) − 1` |
| `return_20d_prior` | `close(as_of)/close(prior20) − 1` |
| `spy_return_5d` | SPY `return_5d_prior` |
| `rs_20d` | `return_20d_prior − spy_return_20d` (internal `spy_return_20d` not a model feature) |
| `drawdown_20d` | `close(as_of) / max(close[prior20..as_of]) − 1` |
| `volatility_5d` | Annualized std of the 5 daily returns in `[prior5..as_of]` |
| `spy_volatility_20d` | `_vol_20d` on SPY closes |

Rejected for this freeze: denser return grids, SMA distance, volume, 60-day windows (would change n). The set was fixed before the run.

## Train Option B gate

```bash
# Requires data/derived/training_events.parquet
uv run python scripts/train_option_b_gate.py
# → data/derived/model_bundle_option_b/ (gitignored)
# → artifacts/runs/option_b_train_<utc>_<id8>.json (write-once)

# Optional Option B smoke (default smoke stays fixture):
MODEL_BUNDLE_DIR=data/derived/model_bundle_option_b \
ALPHAGUARD_REQUIRE_BUNDLE_KIND=option_b \
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke
```

| Pin | Value |
|-----|--------|
| HPO | Train-only `TimeSeriesSplit(n_splits=3)` grid; select by mean val logloss |
| Threshold | Shipped default `train_f1_max` on full-train probs (CLI default in `scripts/train_option_b_gate.py` aligned to `train_f1_max`). `train_val_fbeta_0.5` (`--threshold-fitting`) stays selectable for comparison. |
| `bundle_kind` | `option_b` |
| Library | `src/alphaguard/ml/train_option_b.py` (+ `train_hpo.py` / `train_eval.py`) |

**Sample size:** an early 500-event sample had only 3 test positives, too few to compare models or thresholds (a large train/test F1 gap emits a warning). The sample was expanded to 8,907 deduplicated events ($n_{\text{positive, test}} = 233$) before any gate ran. Results: [`EXPERIMENTS.md`](./EXPERIMENTS.md).

## Builder layout

| Path | Role |
|------|------|
| `scripts/build_training_events.py` | Thin CLI |
| `scripts/run_direct_network.sh` | Unset HTTP proxies; run command |
| `src/alphaguard/ml/dataset_build.py` | Orchestration |
| `src/alphaguard/ml/dataset_ingest.py` | CSV discover / filter / dedup / sample |
| `src/alphaguard/ml/dataset_asof.py` | Calendar + yfinance features/labels |
| `src/alphaguard/ml/dataset_finbert.py` | Offline FinBERT |
| `src/alphaguard/ml/features.py` | **Fixture-only** — must stay FinBERT-free |
| `scripts/train_option_b_gate.py` | Training CLI |
| `scripts/audit_phase_c.py` | Read-only label, fold, leakage, and rules audit |
| `src/alphaguard/ml/train_option_b.py` | Option B train orchestration |
| `src/alphaguard/ml/train_hpo.py` | Nested time-grid HPO |
| `src/alphaguard/ml/train_eval.py` | Threshold + PRF1 helpers |

## Training universe (sample expand, 2026-09-25)

The builder can train on a wider archive ticker set via `--training-universe-file`, while the serving contract (`TICKER_UNIVERSE`, 8 names) stays unchanged.

| Field | Value |
|-------|--------|
| Candidate rule | US-listed; ≥200 deduped headlines in the `001856a6` dev window `[2011-03-02, 2020-02-25]`; yfinance adjusted closes for the full history; top **K=100** + the 6 served names |
| Usable tickers | **106** (100 extras + AAPL, AMZN, GOOGL, META, NVDA, QQQ) |
| Expanded freeze | `data/derived/training_events_expand_ecb73eca.parquet` (file sha `ecb73eca…`, study hash `2e8db9a9…`, **n=201255**) |
| Served rows | **8907** (`served_universe=true`); event IDs and labels match the Option B freeze |
| Evaluation | Primary metrics on the served locked-test rows |
| Split | `nested_time_aware_v1_date_anchor` with the locked-test anchor at `2020-02-25`, so adding rows cannot move the test boundary |
| CLI | `scripts/build_training_events.py --training-universe-file <json> --out <new path>` |

Ticker coverage comes from yfinance, which keeps continuous histories; 881 of 1,772 candidates lacked usable closes and were left out.

## Scope

- The builder produces research training data for the risk model; the Option B bundle exercises the training path (HPO audit + metrics), and the default smoke uses the fixture bundle.
- Smoke and the default pytest run never load FinBERT weights.
- Claim boundaries: [`FINANCE_HONESTY.md`](./FINANCE_HONESTY.md).
