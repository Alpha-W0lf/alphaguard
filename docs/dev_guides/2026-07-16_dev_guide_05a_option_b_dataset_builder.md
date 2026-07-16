# Dev Guide 05a — Option B dataset builder (Kaggle → training_events.parquet)

**Date:** 2026-07-16  
**Repo:** `alphaguard`  
**Work item:** Guide 05a — offline Option B training-row builder (Kaggle source locked; FinBERT batch; **no** XGBoost train)  
**Stage that authored this:** Write-dev-guide (pass 61); Refine-dev-guide (pass 62–64)  
**Status:** **Implement partial** 2026-07-16 — builder+tests+docs landed; live Kaggle download / license paste / full parquet e2e **blocked** (no kaggle CLI creds; network proxy)

**Context SSOT:** `alphaguard/docs/2026-07-15_guide05_option_b_u4_dataset_context_summary.md`  
**Locks:** `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`  
**Prerequisite:** Guides 01–04 shippable. This guide builds the **dataset only**. Guide **05b** (XGBoost train + `bundle_kind=option_b`) is out of scope.

---

## Objective

Build a reproducible offline path that:

1. Downloads (or reads a cached copy of) the locked Kaggle financial-news archive.  
2. Filters to the locked 8-ticker universe.  
3. Deduplicates and samples ≈**500** training rows.  
4. Joins **yfinance** as-of features + **offline FinBERT** sentiment (never during smoke).  
5. Writes `data/training_events.parquet` with ARCHITECTURE §7.5 columns + labels.  
6. Documents regenerate steps and license; updates VISION/ARCHITECTURE honesty (**still not** “Option B trained” / v1 Done).

**Success signal:** A reviewer with Kaggle credentials can regenerate parquet locally; smoke still never loads FinBERT; docs say fixture gate ≠ Option B evidence.

---

## Learning notes (new for this guide)

1. **Training archive ≠ live news** — Kaggle is a static historical dump. Good for reproducible train; bad as a “fresh headlines” product. Live RSS/API is a later path.  
2. **As-of joins (look-ahead bias)** — Price features must use only sessions completed **before** the label window. `feature_as_of` and `published_at` honesty is the interview story (AG3).  
3. **Label vs feature** — `fwd_return_5d` and `label_high_risk` are label-side only. Never put forward return into the feature vector. Volatility may be a **feature** or policy veto, never OR’d into the learned label (AG2).  
4. **Resource mode** — FinBERT + Kafka + Ollama on 16GB thrash. Use `finbert_train`: prefer Compose/Ollama down during batch.

---

## References (paths only)

- `alphaguard/docs/2026-07-15_guide05_option_b_u4_dataset_context_summary.md`
- `alphaguard/docs/ARCHITECTURE.md` (§6.3, §7.5, §8, §11, §15–§16)
- `alphaguard/docs/VISION.md` (Option B row)
- `alphaguard/AGENTS.md`
- `alphaguard/src/alphaguard/contracts/events.py` (`TICKER_UNIVERSE`)
- `alphaguard/scripts/build_fixture_bundle.py` (fixture only — do not confuse with Option B)
- `second_brain/docs/2026-07-16_human_locks_pass60_fan_in.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **Dataset builder only** — no XGBoost train, no `bundle_kind=option_b` manifest, no threshold fitting.  
2. **Source locked:** Kaggle `miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests`.  
3. **Ticker universe locked:** `{AAPL, MSFT, NVDA, GOOGL, AMZN, META, SPY, QQQ}` — reject OOU; no silent remap.  
4. **AG2 / AG3** — forward-downside label only; unified as-of UTC; no future features.  
5. **FinBERT offline only** — never in smoke / default pytest.  
6. **Do not commit** the raw Kaggle dump if license forbids; prefer gitignore + builder download.  
7. Prefer ≤300 lines/file (hard max 400) for new modules.  
8. Same-delivery docs honesty — Option B row = dataset builder landed / train still not started.

---

## Soft pins (locked defaults — do not reopen without human)

| Pin | Locked default |
|-----|----------------|
| Kaggle id | `miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests` |
| CSV discovery | After unzip, discover news CSV under cache (document actual filename in `TRAINING_DATA.md` on first successful download). Required logical columns: `date`, `stock`, `headline` (map `stock` → `ticker`). |
| Target rows | ≈**500** after filter+dedup (honest shortfall OK if documented + `--allow-shortfall`) |
| Sampling | Stratified across universe tickers when enough rows exist; **`random_seed=42`** for reproducibility; else document shortfall |
| Dedup key | `(ticker, calendar_date, normalized_headline)` — keep first occurrence |
| Headline normalize | lower-case; collapse whitespace; strip |
| `published_at` (date-only rows) | Interpret `date` as **America/New_York calendar date**; set `published_at` to that date **09:30 America/New_York** converted to UTC. Rationale: ARCHITECTURE §8 forbids using the same session’s close for features when the headline is intra-day; open-stamp keeps `feature_as_of` on the **prior** completed session. Document in `TRAINING_DATA.md`. |
| `feature_as_of` | Last **fully completed** NYSE regular session at or before `published_at` (ARCHITECTURE §8). Calendar lib: **`exchange_calendars`** session calendar **`XNYS`** (required dependency for this guide). |
| Forward label window | Per §8 item 6: `fwd_return_5d` from first completed session close at/after event session → close 5 trading sessions later |
| Price series | yfinance **adjusted** closes; document in `TRAINING_DATA.md` |
| Label | `label_high_risk = 1` iff `fwd_return_5d < -0.03` else `0` |
| FinBERT model | **`ProsusAI/finbert-tone`** |
| FinBERT input | Headline text only |
| FinBERT score | Map model probs to scalar: **`P(positive) - P(negative)`** ∈ `[-1, 1]` → column `finbert_sentiment`. Do not invent an alternate mapping without a new human soft-pin. |
| CLI entry | **`scripts/build_training_events.py`** (thin) |
| Library home | **`src/alphaguard/ml/dataset_build.py`** (+ split helpers only if needed to stay ≤300 lines/file). **Do not** overload `ml/features.py`. |
| Output | **`data/derived/training_events.parquet`** (repo already gitignores `data/derived/` and `*.parquet`) |
| Raw cache | `data/raw/kaggle_stock_news/` — **add `data/raw/` to `.gitignore`** if missing |
| License record | Implement copies **exact license string** from Kaggle dataset page into `docs/TRAINING_DATA.md` |
| Resource mode | Document `finbert_train`; prefer Kafka/Qdrant/Ollama down during FinBERT |
| Split preview | Print train/test **counts** by time order (80/20); **must not** train the gate |
| `event_id` | `uuid.uuid5(uuid.NAMESPACE_URL, f"alphaguard:train:{ticker}:{calendar_date}:{sha256(normalized_headline)[:16]}")` |

### §7.5 columns required in parquet

`event_id`, `headline`, `ticker`, `published_at`, `feature_as_of`, `finbert_sentiment`, `volatility_20d`, `return_5d_prior`, `return_20d_prior`, `spy_return_5d`, `fwd_return_5d`, `label_high_risk`

Plus provenance columns (**required**): `source_dataset_id` (const Kaggle id string), `source_row_hash` (sha256 of raw row fields), `builder_version` (semver string starting `0.1.0`).

---

## Acceptance criteria (Implement must meet)

- [ ] Kaggle download (or documented offline path) works for a stranger with Kaggle CLI/token  
- [ ] ≈500 rows (or honest shortfall note + exit non-zero / human gate)  
- [ ] All §7.5 columns present; dtypes sane; no NaN labels without documented drop  
- [x] FinBERT runs only in explicit builder command; smoke/pytest default path unchanged  
- [ ] `docs/TRAINING_DATA.md`: license string, regenerate commands, as-of/dedup policy  
- [x] VISION Option B / ARCHITECTURE `ml/train` / README honesty: **dataset builder landed; train not started**; fixture ≠ Option B  
- [x] Unit tests for: OOU reject, dedup, date→published_at, label rule, empty-input fail-closed (mock yfinance/FinBERT where needed)

---

## Ordered step checklist

All boxes start unchecked. **Do not check boxes in Write / Ready-check.**

### Phase A — License + layout

- [ ] **A1.** Open Kaggle dataset page; copy license/access text into `docs/TRAINING_DATA.md`.  
- [x] **A2.** Ensure `.gitignore` covers `data/raw/` (add if missing). Confirm `data/derived/` / `*.parquet` already ignored.  
- [x] **A3.** Add thin `scripts/build_training_events.py` + `src/alphaguard/ml/dataset_build.py` (split helpers only to stay ≤300 lines). Do not put FinBERT into `ml/features.py`.  
- [x] **A4.** Add `exchange_calendars` (and builder deps) to project dependency file; document in `TRAINING_DATA.md`.

### Phase B — Ingest + filter

- [ ] **B1.** Download/unzip via Kaggle CLI (document exact commands + discovered CSV name).  
- [x] **B2.** Parse `date`/`stock`/`headline`; map to universe; drop OOU with counts.  
- [x] **B3.** Apply dedup + stratified sample ≈500 with `seed=42`.  
- [x] **B4.** Assign stable `event_id` per soft pin.

### Phase C — As-of features + labels

- [x] **C1.** Implement NYSE completed-session `feature_as_of` per §8 + open-stamp `published_at`.  
- [x] **C2.** yfinance adjusted closes for feature columns + `fwd_return_5d`; drop rows that cannot label honestly.  
- [x] **C3.** Compute `label_high_risk` from soft pin.  
- [x] **C4.** Unit tests: Tuesday morning headline must not use Tuesday close as a **feature**; label window may use post-event closes.

### Phase D — FinBERT batch

- [x] **D1.** Offline batch; write `finbert_sentiment` via soft-pin mapping; resume/idempotent if mid-batch fail.  
- [x] **D2.** Document RAM guidance: stop Compose/Ollama during batch.  
- [x] **D3.** Prove default smoke/pytest does **not** import FinBERT weights (`rg` / import guard).

### Phase E — Output + docs

- [ ] **E1.** Write `data/derived/training_events.parquet`; print row counts by ticker + 80/20 time-split counts.  
- [x] **E2.** Update VISION / ARCHITECTURE / README / AGENTS honesty.  
- [x] **E3.** Stop. **Do not** train XGBoost (Guide 05b).

---

## Verification / Definition of Done

```bash
# From alphaguard/
# With Kaggle credentials configured:
#   kaggle datasets download -d miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests -p data/raw/kaggle_stock_news --unzip
uv run python scripts/build_training_events.py
python -c "import pandas as pd; df=pd.read_parquet('data/derived/training_events.parquet'); print(len(df), sorted(df.columns.tolist()))"
uv run pytest -q
ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture make smoke
rg -n 'ProsusAI/finbert|finbert' src/alphaguard/ml/features.py || true   # must stay FinBERT-free
rg -n 'Option B|training_events|finbert_train|fixture bundle' docs/VISION.md docs/ARCHITECTURE.md README.md docs/TRAINING_DATA.md
```

**DoD:** Builder green; §7.5 columns; license documented; smoke FinBERT-free; `features.py` unchanged as fixture-only; no Option B train claims; Guide 05b not started.

---

## Blast radius and risks

| Risk | Blast radius | Mitigation |
|------|--------------|------------|
| License violation | Public repo legal risk | Record license; don’t commit raw dump if forbidden |
| Look-ahead in yfinance join | False ML story | §8 tests; document series |
| RAM thrash | Laptop unusable | `finbert_train` ops note |
| Scope into XGBoost | Calendar burn | Hard stop after parquet |
| Claiming Option B from fixture | Interview fail | Docs + future fail-closed on bundle_kind |

### Rollback

Delete generated parquet/raw cache; revert builder commits; smoke must still pass.

---

## Edge-case handling

| Case | Required behavior |
|------|-------------------|
| Missing ticker / unmappable | Drop + count |
| Duplicate headlines | Dedup soft pin |
| yfinance gap / delist | Drop row; do not invent prices |
| FinBERT partial failure | Resume or fail closed with clear error; no silent half-file as success |
| &lt;500 after filters | Document shortfall; non-zero exit or explicit `--allow-shortfall` flag requiring human |
| Ambiguous / missing date | Reject row; do not invent |
| Same-session feature peek | Fail unit test (ARCHITECTURE §8 example) |

---

## Stop conditions

- Parquet + TRAINING_DATA.md + honesty docs landed  
- **Do not** start Guide 05b train  
- **Do not** reopen Kafka Guide 04  
- **Do not** claim v1 / Option B model complete  

---

## Refine pass 62 notes

- Fixed date-only `published_at` soft pin (open stamp, not close stamp) to match §8.  
- Pinned builder layout, output path under `data/derived/`, FinBERT score mapping, sampling seed, calendar library.  
- Explicit: do not load FinBERT via `ml/features.py`.

---

## Ready for Ready-check?

**Yes.** Ready-check readiness score: **8.7 / 10**.  
Not 10: Implement still discovers the real Kaggle CSV filename, runs live yfinance/FinBERT, and copies license text from the Kaggle page. Those are runtime proofs, not missing design forks.
