# Dev Guide — Thin Soft Adjust: FB→META universe alias (train hygiene)

**Date:** 2026-07-21  
**Repo:** `alphaguard`  
**Work item:** Graceful FB→META archive alias for Option B training ingest (post-MV hygiene / senior-demo rigor)  
**Stage that authored this:** Write-dev-guide (pass 164n spoke)  
**Status:** **Soft Adjust (2026-07-21 hub)** — Tom authorized Implement: alias **registry** `FB→META` + `GOOG→GOOGL` **including parquet + Option B rebuild**. Prior Write locks that said GOOG-out / builder-only are **superseded** by that authorize phrase.

**Justify thin guide:** TRAINING_DATA already drafts the alias pricing rule; ingest already reports `alias_candidates_oou`; Soft Adjust expands to a small versioned registry (not a new Guide 09 product surface).

**Context / hub:**  
- `second_brain/docs/2026-07-21_spoke_alphaguard_fb_meta_write_dev_guide_pass164n_handoff.md`  
- `second_brain/docs/2026-07-21_alphaguard_senior_demo_prioritize_pass164n.md` (T1-E)  
- `second_brain/docs/2026-07-21_alphaguard_portfolio_finance_rigor_gather_pass164n_context_summary.md`  
**Rule draft SSOT:** `alphaguard/docs/TRAINING_DATA.md` (Alias pricing rule + Yahoo FB≠Meta evidence)  
**Prerequisite:** Guides 05a/05b Review shippable; Align T1-A/B/C Met (`156586f`). Default smoke still fixture.

**Human locks (pass 164n — do not reopen):**

| Lock | Value |
|------|--------|
| Unify FB/META | **Yes** — Tom rejected parking; graceful coded alias |
| Archive map | `stock=FB` → training `ticker=META` |
| Price fetch | **`META` only** — never Yahoo `FB` (wrong instrument today) |
| Missing META series | **Fail closed** for required window / rows that need prices |
| Provenance | Record alias applied (counts + rule version); not silent |
| GOOG→GOOGL | **In** — `goog_googl_v1` (hub Soft Adjust 2026-07-21; Tom wants rename registry) |
| Rebuild | **In** — regenerate `training_events.parquet` + Option B train; update honesty metrics |
| Character | No brokerage, no PnL claims, no Guide 09 invent as required MV |
| Build DoD | Remains declared MV Met — this is **post-MV** train hygiene |

---

## Objective

Soft-pin and implement a **documented, fail-closed, provenance-backed** training-ingest alias so Facebook-era archive rows (`stock=FB`) become locked-universe `ticker=META` rows, with closes fetched as **META only**.

**Success signal:** With aliases on, preferred CSV yields META + GOOGL training rows from archive `FB`/`GOOG`; unit tests prove registry on/off + “never fetch FB/GOOG”; one-line join probe documented in DoD; TRAINING_DATA / honesty surfaces updated after parquet + Option B rebuild. Smoke / fixture path unchanged.

---

## Learning notes (interview prep)

1. **Corporate-action / ticker rename vs silent remapping** — Archives often keep the historical listing symbol (`FB`). Serving/universe contracts use the current symbol (`META`). An explicit, versioned alias with provenance is audit-safe; a silent map looks like leakage or cherry-picking to reviewers.  
2. **Symbol collision risk** — Yahoo remapped free-text `FB` to an unrelated ETF. Fetching the wrong instrument poisons labels/features (look-ahead / wrong-asset bias). Fail closed beats “best effort.”  
3. **Train/serve symbol skew** — Training rows must use the same ticker string the live gate/universe expects (`META` ∈ `TICKER_UNIVERSE`), while `source_row_hash` still fingerprints the raw archive row (`stock=FB`).  
4. **Fail closed vs fail open** — Security- and label-integrity paths fail closed (reject/drop/error). Observability spans may fail open; price identity must not.

---

## References (paths only)

- `alphaguard/docs/TRAINING_DATA.md`
- `alphaguard/docs/ARCHITECTURE.md` (§7.1 universe / no silent remap; §7.5 training row)
- `alphaguard/docs/FINANCE_HONESTY.md`
- `alphaguard/docs/VISION.md` (ticker universe)
- `alphaguard/src/alphaguard/contracts/events.py` (`TICKER_UNIVERSE`)
- `alphaguard/src/alphaguard/ml/dataset_ingest.py`
- `alphaguard/src/alphaguard/ml/dataset_build.py`
- `alphaguard/src/alphaguard/ml/dataset_asof.py` (`default_yfinance_closes`, `make_cached_close_fetcher`)
- `alphaguard/tests/test_dataset_build.py` (`test_ingest_reports_absent_universe_and_fb_alias_candidate`)
- `alphaguard/docs/dev_guides/2026-07-16_dev_guide_05a_option_b_dataset_builder.md`
- `second_brain/docs/2026-07-21_spoke_alphaguard_fb_meta_write_dev_guide_pass164n_handoff.md`
- `second_brain/docs/workflow_os/rails/QUALITY_STANDARD.md`

---

## Architecture constraints (binding)

1. **§7.1 “no silent remap” still holds** — This Soft Adjust is **not** silent: it is a locked, versioned archive→universe alias with operator counts + provenance. Live fixtures / RSS / replay continue to reject OOU tickers; do **not** accept raw `FB` on ingress contracts.  
2. **Training ingest only** — Alias applies in `dataset_ingest` (Kaggle CSV path), not in `NewsEvent` validation, RSS normalize, or fixture loaders.  
3. **Price identity** — After remap, `compute_features_and_label` / yfinance must receive `META`. Add an explicit guard so `FB` never reaches `default_yfinance_closes` / cached fetcher for this builder path.  
4. **AG2 / AG3 unchanged** — Label remains forward downside only; as-of join still uses XNYS; non-sessions drop as today — probe must not invent closes.  
5. **GOOG→GOOGL Soft Adjust (2026-07-21)** — Apply `goog_googl_v1` the same way as FB→META (before universe filter; provenance; `source_row_hash` on raw `GOOG`). Prices fetch as **`GOOGL` only**.  
6. **No MSFT/SPY invention** — Absent tickers remain honesty gaps.  
7. Prefer ≤300 lines/file (hard max 400); smallest correct change.  
8. Same-delivery docs honesty after Implement — TRAINING_DATA + FINANCE_HONESTY (and thin ARCHITECTURE note if needed) must match coded behavior.

---

## Soft pins (locked defaults — do not reopen without human)

| Pin | Locked default |
|-----|----------------|
| Registry | Versioned table: `fb_meta_v1` (`FB`→`META`), `goog_googl_v1` (`GOOG`→`GOOGL`); extensible pattern |
| Default | Aliases **on** for canonical builder (`load_filter_dedup_sample` default / production CLI path) |
| Toggle for honesty tests | Keyword `apply_archive_aliases: bool = True`; tests must exercise `False` |
| When applied | After normalize/upper `stock`→`ticker`, **before** `isin(TICKER_UNIVERSE)` filter |
| `source_row_hash` | Still hash **raw** `date|stock|headline` (archive symbol, e.g. `FB` / `GOOG`, in hash input) |
| `event_id` | Use **post-alias** universe ticker (`META` / `GOOGL`) |
| `builder_version` | Bump patch (e.g. `0.1.0` → `0.1.1`) when registry lands — document in TRAINING_DATA |
| Stats / provenance | `IngestStats`: `alias_rule_version` (e.g. `fb_meta_v1+goog_googl_v1` when on), `alias_applied_counts` (`{"FB→META": N, "GOOG→GOOGL": M}`), `alias_candidates_oou` for **unapplied** registry sources only |
| Operator log | Print rule version + applied counts (and “alias off” when disabled) |
| Price fetch | Never call yfinance with archive sources `FB` or `GOOG` on builder path; raise if fetcher invoked with them — fetch **`META` / `GOOGL` only** |
| Fail closed | Empty target series → row drops; if **all** sampled rows drop after as-of/label join, RuntimeError must mention active alias rules / target tickers |
| Join probe (DoD) | Documented one-liner / `scripts/probe_fb_meta_join.py` — META close coverage for FB headline days; **does not invent** closes; never downloads `FB` |
| Stratified sample | After alias, META / GOOGL participate like other universe tickers |
| Canonical rebuild | **In** — regenerate parquet + Option B train + honesty metrics (Tom authorize 2026-07-21) |

### Suggested ingest shape (Implement fills exact names; meaning locked)

```text
# Pseudocode — registry table, not ad-hoc ifs forever
REGISTRY = [("fb_meta_v1","FB","META"), ("goog_googl_v1","GOOG","GOOGL")]
ticker = stock.strip().upper()
if apply_archive_aliases and ticker in registry_sources:
    apply map; count "SRC→DST"; provenance rule ids
else if ticker in registry_sources:
    alias_candidates_oou[ticker] += 1  # honesty when off
# then universe filter as today
```

### Suggested price guard (builder / asof Soft Adjust)

```text
# In default_yfinance_closes or make_cached_close_fetcher (builder path):
if ticker in {"FB", "GOOG"}:  # archive sources — fetch META / GOOGL only
    raise ValueError("...")
```
---

## Acceptance criteria (Implement must meet)

- [x] Aliases **on**: `stock=FB` → `ticker=META`; `stock=GOOG` → `ticker=GOOGL`; both survive universe filter; META/GOOGL not absent solely because archive symbols were dropped  
- [x] Aliases **off**: FB/GOOG remain OOU; `alias_candidates_oou` counts both; META absent if no native META (honesty path)  
- [x] No yfinance/`fetch_closes` call with `FB` or `GOOG` on builder path (unit-tested with guard and/or fake fetcher)  
- [x] Provenance: rule version + applied counts in stats/log; `builder_version` bumped  
- [x] Fail-closed behavior documented + tested for empty META series when FB-origin rows required prices  
- [x] One-line join probe in DoD / TRAINING_DATA (coverage honesty; no invented closes)  
- [x] Unit tests updated/added; `uv run pytest -q` green  
- [x] Docs: TRAINING_DATA alias registry **soft-pinned / coded**; FINANCE_HONESTY updated after rebuild; thin §7.1 note that **documented training aliases** ≠ silent remap  
- [x] Parquet + Option B regenerated; honest metrics recorded; no MSFT/SPY invention; no brokerage/PnL; no Guide 09 invent; smoke still fixture  

---

## Ordered step checklist

### Phase A — Ingest alias registry + provenance

- [x] **A1.** Add versioned registry table: `fb_meta_v1` FB→META, `goog_googl_v1` GOOG→GOOGL (extensible).  
- [x] **A2.** Extend `load_filter_dedup_sample(..., apply_archive_aliases: bool = True)`. Apply registry **before** universe filter; count applied.  
- [x] **A3.** Extend `IngestStats` with `alias_rule_version: str` and `alias_applied_counts: dict[str, int]` (empty when none / alias off). `alias_candidates_oou` = unapplied registry sources only.  
- [x] **A4.** Bump `BUILDER_VERSION` patch; keep `source_row_hash` on raw stock; `event_id` on post-alias ticker.  
- [x] **A5.** Update `dataset_build.py` operator prints: documented aliases + counts; clarify WARNING so “no silent remap” is not contradicted.

### Phase B — Price identity fail-closed

- [x] **B1.** Guard yfinance/cached fetcher: reject archive sources `FB` and `GOOG`.  
- [x] **B2.** Confirm post-alias rows call `compute_features_and_label` with `META` / `GOOGL`.  
- [x] **B3.** Strengthen all-drop RuntimeError to mention active alias rules / target tickers. Soft Adjust only — do not redesign as-of.

### Phase C — Tests

- [x] **C1.** Default alias **on**: META present from FB; GOOGL from GOOG; applied counts; FB/GOOG not in sampled tickers.  
- [x] **C2.** `apply_archive_aliases=False` → FB/GOOG OOU + candidate counts; META absent if no native META.  
- [x] **C3.** Alias on + fake `fetch_closes` — never `"FB"`/`"GOOG"`; META/GOOGL requested for aliased rows.  
- [x] **C4.** Empty META series → fail closed / no silent META coverage (match B3).  
- [x] **C5.** Assert `goog_googl_v1` applies when on (GOOG→GOOGL); when off, GOOG stays candidate.

### Phase D — Docs + join probe

- [x] **D1.** Update `TRAINING_DATA.md`: registry **soft-pinned coded**; default on; toggle; builder_version; refresh live evidence after rebuild.  
- [x] **D2.** Add / keep **one-line join probe** in TRAINING_DATA DoD.  
- [x] **D3.** Thin ARCHITECTURE §7.1: training ingest may apply **explicit documented archive aliases** (`fb_meta_v1`, `goog_googl_v1`); fixtures/live still no silent remap.  
- [x] **D4.** FINANCE_HONESTY: update lab metrics after parquet + Option B rebuild.  
- [x] **D5.** Optional one-liner cross-link — do not rewrite 05a history as if alias always existed.

### Phase E — Canonical rebuild (locked in)

- [x] **E1.** Regenerate `training_events.parquet` via `./scripts/run_direct_network.sh` + FinBERT; re-run Option B train; update TRAINING_DATA + FINANCE_HONESTY.  
- [x] **E2.** ~~Builder-only~~ — superseded by Tom authorize including rebuild.

### Phase F — Verification + stop

- [x] **F1.** `uv run pytest -q` green.  
- [x] **F2.** Run join probe (network may require `run_direct_network.sh`).  
- [x] **F3.** Stop for Review. No Guide 09 / agent-on-consume / brokerage / MSFT-SPY invention.

---

## Verification / Definition of Done

**Done when all are true:**

1. Documented registry `fb_meta_v1` + `goog_googl_v1` coded with default **on**; toggleable **off** for honesty tests.  
2. Prices for aliased rows use **META** / **GOOGL** only; `FB`/`GOOG` fetch guarded/fail-closed.  
3. Provenance: rule version + applied counts in stats/log; `builder_version` bumped.  
4. Unit tests cover aliases on, aliases off, no FB/GOOG fetch, GOOG→GOOGL when on.  
5. Join probe documented (and runnable) for META close coverage vs FB headline days — **no invented closes**.  
6. Docs match code (TRAINING_DATA + thin ARCHITECTURE note + FINANCE_HONESTY after rebuild).  
7. Parquet + Option B regenerated with honest metrics.  
8. Character preserved: post-MV hygiene only; smoke fixture; no PnL/brokerage/Guide 09 invent.

**Explicitly not required:**

- Live Kaggle download in CI  
- Changing default smoke to Option B  
- MSFT/SPY backfill  
- Hosted deploy / agent-on-consume  

**Suggested verification commands:**

```bash
# From alphaguard/
uv run pytest -q tests/test_dataset_build.py
uv run pytest -q

# Join probe (DoD one-liner — Implement may Soft Adjust exact script;
# intent: FB headline calendar days ∩ META adjusted closes; report coverage fraction.
# Prefer run_direct_network.sh if Cursor proxy breaks yfinance.)
./scripts/run_direct_network.sh uv run python - <<'PY'
# Soft Adjust allowed: small scripts/probe_fb_meta_join.py instead of heredoc.
# Must: read preferred CSV FB dates; fetch META closes only; print
#   fb_days=N meta_same_day_closes=M coverage=M/N
# Must not: download ticker FB; invent closes for non-sessions.
print("see TRAINING_DATA.md join probe — implement probe_fb_meta_join or inline")
PY
```

**Reference evidence already in TRAINING_DATA (2026-07-16):** local FB headlines 389 rows; 86 unique ET days; **77/86** same-day META close (rest non-sessions — as-of join drops/shifts). Probe after Implement should reconfirm under current Yahoo behavior (not a forever guarantee).

---

## Blast radius and risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Yahoo `FB` fetch if guard missed | Wrong-asset labels (ETF) | Hard reject `FB` in fetcher; unit test |
| Silent remap perception | Reviewer distrust / “cheating” | Provenance + ARCHITECTURE wording + logs |
| Rebuild changes Option B metrics | Stale FINANCE_HONESTY | E1 same-delivery honesty update **or** E2 no metric claims |
| Stratified sample shifts | Different 500-row draw | Document seed still 42; expect ticker mix change; unique `event_id` still required |
| `event_id` identity change for FB-origin rows | Parquet not comparable row-for-row to pre-alias | Expected; bump builder_version; regenerate |
| Over-broad alias helper | Accidental remap of unrelated symbols | Registry table only; unit tests per rule |
| Live ingress accepts `FB` | Contract break | Alias **training ingest only** |
| Join probe invents closes | False coverage | Probe reports intersection only; non-sessions OK to miss |

---

## Edge-case handling

| Case | Required behavior |
|------|-------------------|
| Native `META` rows + `FB` rows | Both become META; dedup on `(META, calendar_date, normalized_headline)` keep first |
| Alias on, zero FB rows | `alias_applied_counts` empty or zero; no error |
| Alias off, FB present | FB dropped as OOU; candidate count; META absent if no native META |
| Empty / delisted META window | Fail closed for required join (B3) |
| Non-session FB headline day | As-of join drops/shifts as today — probe must not invent a close |
| `stock` casing `fb` / `Fb` | Uppercase then alias |
| Duplicate headlines FB vs META same day | Dedup after alias |
| Fixture / RSS `FB` | Still reject OOU — **out of scope to accept** |
| Cursor proxy 403 on yfinance | Use `run_direct_network.sh` (existing TRAINING_DATA note) |

---

## Out of scope (stop list)

- Inventing MSFT/SPY rows  
- Brokerage APIs, PnL claims, Lowd Capital  
- Guide 09 / agent-on-consume / hosted deploy  
- Changing live `NewsEvent` / fixture loaders to accept `FB` / `GOOG`  
- Optuna / neural reranker / second LLM auditor  
- Review implementation stage (hub after Results)

---

## Open decisions (human — surface in chat; do not invent locks)

**None blocking.** Locked 2026-07-21 by Tom authorize phrase:  
`Authorize Implement FB→META+GOOG→GOOGL alias registry including parquet+Option B rebuild`

Soft residual: if rebuild env/network flakes, park rebuild with evidence and stop for hub — do not invent metrics.

---

## Honest readiness

- **Implement:** In progress under locked authorize (registry + rebuild).  
- **Ready for:** Review after Implement DoD Met + handoff Results filled.  
- **Will not:** Expand to MSFT/SPY invention; accept live FB/GOOG ingress; start Review in this spoke unless DoD fully Met.

## QUALITY self-check (§5)

- [x] Steps, DoD, blast radius, edge cases present  
- [x] Locks frozen; Soft Adjust bounded; architecture conflict addressed (explicit ≠ silent)  
- [x] No code implemented this stage  
- [x] Spoke stayed in FB→META Write slice  
- [x] Open human decisions listed with recommendation + tradeoffs  
