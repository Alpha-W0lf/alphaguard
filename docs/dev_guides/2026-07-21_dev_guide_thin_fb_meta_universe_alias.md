# Dev Guide — Thin Soft Adjust: FB→META universe alias (train hygiene)

**Date:** 2026-07-21  
**Repo:** `alphaguard`  
**Work item:** Graceful FB→META archive alias for Option B training ingest (post-MV hygiene / senior-demo rigor)  
**Stage that authored this:** Write-dev-guide (pass 164n spoke)  
**Status:** **Write complete — not Implemented** (no code in this stage)

**Justify thin guide:** TRAINING_DATA already drafts the alias pricing rule; ingest already reports `alias_candidates_oou["FB"]`; this soft-pins **one** explicit remap with provenance — not a new Guide 09 product surface.

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
| GOOG→GOOGL | **Out of this slice** (leave GOOG as OOU watch only) |
| Character | No brokerage, no PnL claims, no Guide 09 invent as required MV |
| Build DoD | Remains declared MV Met — this is **post-MV** train hygiene |

---

## Objective

Soft-pin and implement a **documented, fail-closed, provenance-backed** training-ingest alias so Facebook-era archive rows (`stock=FB`) become locked-universe `ticker=META` rows, with closes fetched as **META only**.

**Success signal:** With alias on, preferred CSV yields META training rows (not zero); unit tests prove alias on/off + “never fetch FB”; one-line join probe documented in DoD; TRAINING_DATA / honesty surfaces updated; GOOG still OOU (watch counts only). Smoke / fixture path unchanged.

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
5. **GOOG stays OOU** — Continue reporting `alias_candidates_oou["GOOG"]`; do **not** map to `GOOGL` in this slice.  
6. **No MSFT/SPY invention** — Absent tickers remain honesty gaps.  
7. Prefer ≤300 lines/file (hard max 400); smallest correct change.  
8. Same-delivery docs honesty after Implement — TRAINING_DATA + FINANCE_HONESTY (and thin ARCHITECTURE note if needed) must match coded behavior.

---

## Soft pins (locked defaults — do not reopen without human)

| Pin | Locked default |
|-----|----------------|
| Alias rule id | `fb_meta_v1` |
| Map | archive `stock`/`ticker` **`FB` → `META`** only |
| Default | Alias **on** for canonical builder (`load_filter_dedup_sample` default / production CLI path) |
| Toggle for honesty tests | Keyword `apply_fb_meta_alias: bool = True`; tests must exercise `False` |
| When applied | After normalize/upper `stock`→`ticker`, **before** `isin(TICKER_UNIVERSE)` filter |
| `source_row_hash` | Still hash **raw** `date|stock|headline` (stock remains `FB` in hash input) |
| `event_id` | Use **post-alias** `ticker=META` (universe identity) |
| `builder_version` | Bump patch (e.g. `0.1.0` → `0.1.1`) when alias lands — document in TRAINING_DATA |
| Stats / provenance | `IngestStats` (or equivalent) must expose: `alias_rule_version`, `alias_applied_counts` (at least `{"FB→META": N}`), keep `alias_candidates_oou` for **unapplied** watches (`GOOG`; and `FB` when alias off) |
| Operator log | Print one clear line: rule version + FB→META count (and “alias off” when disabled) |
| Price fetch | Never call yfinance with `FB` on builder path; Soft Adjust: raise `ValueError` / `RuntimeError` if fetcher is invoked with `FB` |
| Fail closed | If alias on and META closes empty for the window needed by as-of/label join → row drops as today; if **all** aliased META rows drop for empty series (or cache miss empty for META when FB rows existed), fail closed with explicit error (do not write parquet claiming META coverage) |
| Join probe (DoD) | Documented one-liner (see Verification) — must run or be runnable; reports META close coverage for FB headline calendar days; **does not invent** closes |
| Stratified sample | After alias, META participates like other universe tickers |
| Canonical rebuild | **Open decision** (see below) — guide supports both; Implement must follow Tom lock |

### Suggested ingest shape (Implement fills exact names; meaning locked)

```text
# Pseudocode — not to paste blindly
ticker = stock.strip().upper()
# watch counts for honesty (GOOG always; FB when alias off)
if apply_fb_meta_alias and ticker == "FB":
    ticker = "META"
    alias_applied_counts["FB→META"] += 1
# then universe filter as today
```

### Suggested price guard (builder / asof Soft Adjust)

```text
# In default_yfinance_closes or make_cached_close_fetcher (builder path):
if ticker == "FB":
    raise ValueError("Yahoo FB is not Meta — fetch META only (fb_meta_v1)")
```

---

## Acceptance criteria (Implement must meet)

- [ ] Alias **on**: CSV rows with `stock=FB` become `ticker=META` and survive universe filter; `META` no longer listed in `universe_tickers_absent` solely because FB was dropped  
- [ ] Alias **off**: FB remains OOU; `alias_candidates_oou["FB"]` counted; META absent if no native META rows (honesty path)  
- [ ] GOOG never remapped; still counted in `alias_candidates_oou` when present  
- [ ] No yfinance/`fetch_closes` call with ticker `FB` on builder path (unit-tested with fake fetcher or guard)  
- [ ] Provenance: rule version + applied count visible in stats and/or build log; `builder_version` bumped  
- [ ] Fail-closed behavior documented + tested for empty META series when FB rows required prices  
- [ ] One-line join probe in DoD / TRAINING_DATA (coverage honesty; no invented closes)  
- [ ] Unit tests updated/added; `uv run pytest -q` green  
- [ ] Docs: TRAINING_DATA alias rule marked **soft-pinned / coded**; FINANCE_HONESTY thin honesty if Option B metrics change; thin §7.1 note that **documented training aliases** ≠ silent remap  
- [ ] No GOOG→GOOGL; no MSFT/SPY invention; no brokerage/PnL; no Guide 09 invent; smoke still fixture  

---

## Ordered step checklist

### Phase A — Ingest alias + provenance

- [ ] **A1.** Add locked constants: `ALIAS_RULE_VERSION = "fb_meta_v1"` (module-level in `dataset_ingest.py` or tiny helper).  
- [ ] **A2.** Extend `load_filter_dedup_sample(..., apply_fb_meta_alias: bool = True)`. Apply FB→META **before** universe filter; count applied; keep GOOG watch-only.  
- [ ] **A3.** Extend `IngestStats` with `alias_rule_version: str` and `alias_applied_counts: dict[str, int]` (empty dict when none / alias off). Preserve `alias_candidates_oou` semantics: unapplied OOU rename candidates only.  
- [ ] **A4.** Bump `BUILDER_VERSION` patch; keep `source_row_hash` on raw stock; `event_id` on post-alias ticker.  
- [ ] **A5.** Update `dataset_build.py` operator prints: alias rule + counts; clarify WARNING text so “no silent remap” is not contradicted (say “documented alias fb_meta_v1 applied” when on).

### Phase B — Price identity fail-closed

- [ ] **B1.** Guard yfinance/cached fetcher (or builder wrapper): reject ticker `FB`.  
- [ ] **B2.** Confirm post-alias rows call `compute_features_and_label(ticker="META", ...)`.  
- [ ] **B3.** Fail closed if META series empty when aliased FB rows cannot join (explicit error or documented all-drop RuntimeError already present — strengthen message to mention `fb_meta_v1` / META). Soft Adjust only — do not redesign as-of.

### Phase C — Tests

- [ ] **C1.** Update `test_ingest_reports_absent_universe_and_fb_alias_candidate`: with **default alias on**, expect META present / FB applied count; GOOG still candidate; optionally assert FB not in sampled tickers.  
- [ ] **C2.** New test: `apply_fb_meta_alias=False` → FB OOU, META absent, `alias_candidates_oou["FB"]==1` (honesty / fail-closed-off path).  
- [ ] **C3.** New test: alias on + fake `fetch_closes` — assert fetch tickers ⊆ universe and never `"FB"`; META requested for FB-origin rows.  
- [ ] **C4.** New test: empty META series → fail closed / no silent success claiming META coverage (match B3).  
- [ ] **C5.** Assert GOOG→GOOGL does **not** occur (GOOG dropped; GOOGL count unchanged by FB alias).

### Phase D — Docs + join probe

- [ ] **D1.** Update `TRAINING_DATA.md`: mark alias pricing rule **soft-pinned coded** (`fb_meta_v1`); document default on; toggle for tests; builder_version bump; refresh universe table expectations after rebuild **or** note “coded; regenerate parquet to refresh live evidence.”  
- [ ] **D2.** Add / keep **one-line join probe** in TRAINING_DATA DoD (see Verification).  
- [ ] **D3.** Thin ARCHITECTURE §7.1 clarification: training ingest may apply **explicit documented archive aliases** (list `fb_meta_v1`); fixtures/live still no silent remap.  
- [ ] **D4.** FINANCE_HONESTY: if Implement rebuilds Option B parquet+train, update lab metrics honesty; if builder-only, note META coverage may appear only after regenerate.  
- [ ] **D5.** Optional one-liner in Guide 05a status or TRAINING_DATA cross-link — do not rewrite 05a history as if alias always existed.

### Phase E — Optional canonical rebuild (Tom gate)

- [ ] **E1.** If Tom locks **rebuild in same delivery:** regenerate `training_events.parquet` via `./scripts/run_direct_network.sh` + FinBERT path; re-run Option B train; update TRAINING_DATA live evidence + FINANCE_HONESTY metrics.  
- [ ] **E2.** If Tom locks **builder+docs+tests first:** stop after D; leave regenerate as explicit follow-up. Do not claim live parquet already contains META.

### Phase F — Verification + stop

- [ ] **F1.** `uv run pytest -q` green.  
- [ ] **F2.** Run or dry-run join probe command from Verification (network may require `run_direct_network.sh`).  
- [ ] **F3.** Stop. No Guide 09 / agent-on-consume / GOOG remap / brokerage.

---

## Verification / Definition of Done

**Done when all are true:**

1. Documented `fb_meta_v1` alias coded with default **on**; toggleable **off** for honesty tests.  
2. Prices for aliased rows use **META only**; `FB` fetch guarded/fail-closed.  
3. Provenance: rule version + applied counts in stats/log; `builder_version` bumped.  
4. Unit tests cover alias on, alias off, no FB fetch, no GOOG→GOOGL.  
5. Join probe documented (and runnable) for META close coverage vs FB headline days — **no invented closes**.  
6. Docs match code (TRAINING_DATA + thin ARCHITECTURE note; FINANCE_HONESTY if metrics/rebuild).  
7. Character preserved: post-MV hygiene only; smoke fixture; no PnL/brokerage/Guide 09 invent.

**Explicitly not required (unless Tom locks E1):**

- Live Kaggle download in CI  
- Changing default smoke to Option B  
- MSFT/SPY backfill  
- GOOG→GOOGL  
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
| Over-broad alias helper | Accidental GOOG→GOOGL | Hard-code FB→META only; test GOOG untouched |
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

- Implement / train re-run in **this Write stage**  
- GOOG→GOOGL (unless Tom re-locks with evidence)  
- Inventing MSFT/SPY rows  
- Brokerage APIs, PnL claims, Lowd Capital  
- Guide 09 / agent-on-consume / hosted deploy  
- Changing live `NewsEvent` / fixture loaders to accept `FB`  
- Optuna / neural reranker / second LLM auditor  

---

## Open decisions (human — surface in chat; do not invent locks)

### 1. GOOG→GOOGL in this guide?

- **In plain terms:** Alphabet has archive `GOOG` (class C) and universe `GOOGL`. Include a second alias now, or FB→META only?  
- **Options:** (A) FB→META only · (B) Also GOOG→GOOGL in same Soft Adjust  
- **Recommendation:** **(A)** — hub default; GOOG/GOOGL are related but not the same rename story as FB→META; keep blast radius small.  
- **Tradeoffs:** (A) leaves Alphabet split honesty; (B) more coverage, more review heat on “silent remap.”  
- **Needs from you:** Confirm **A** (default) or lock **B**.

### 2. Rebuild Option B parquet + train in the same Implement delivery?

- **In plain terms:** After coding the alias, should Implement also regenerate the gitignored parquet and retrain Option B so live evidence shows META, or ship builder+tests+docs first?  
- **Options:** (A) Builder + unit tests + docs only · (B) Same delivery: regenerate parquet + Option B train + honesty metric update  
- **Recommendation:** **(A)** first if calendar is tight — proves fail-closed alias without FinBERT/network coupling; authorize **(B)** as immediate follow-up Implement or Soft Adjust Phase E when Tom wants demo evidence. Prefer **(B)** if the next demo must show META in parquet ticker mix.  
- **Tradeoffs:** (A) faster, docs must say “regenerate to refresh evidence”; (B) fuller honesty, longer / flakier (FinBERT, Yahoo, proxy).  
- **Needs from you:** `Authorize Implement builder+tests+docs only` or `Authorize Implement including parquet+Option B rebuild`.

---

## Honest readiness

- **Write-dev-guide:** Met when this file + handoff Results filled.  
- **Ready for:** Refine-dev-guide **or** Ready check before code (after Tom locks open decisions, or Ready-check proceeds with defaults A + A).  
- **Not ready for:** Implement until Ready-check / human authorize (and decision 2 locked if delivery shape matters).  
- **Will not:** Implement in this stage; expand to GOOG without lock; park FB→META.

## QUALITY self-check (§5)

- [x] Steps, DoD, blast radius, edge cases present  
- [x] Locks frozen; Soft Adjust bounded; architecture conflict addressed (explicit ≠ silent)  
- [x] No code implemented this stage  
- [x] Spoke stayed in FB→META Write slice  
- [x] Open human decisions listed with recommendation + tradeoffs  
