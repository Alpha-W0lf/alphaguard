# Ready-check note — Thin Soft Adjust: FB→META universe alias (pass 164n)

**Date:** 2026-07-21  
**Repo:** `alphaguard`  
**Mode:** spoke  
**Stage:** Ready check before code only  
**Guide:** `docs/dev_guides/2026-07-21_dev_guide_thin_fb_meta_universe_alias.md`  
**Handoff:** `second_brain/docs/2026-07-21_spoke_alphaguard_fb_meta_ready_check_pass164n_handoff.md`  
**Write handoff:** `second_brain/docs/2026-07-21_spoke_alphaguard_fb_meta_write_dev_guide_pass164n_handoff.md`  
**Fan-in:** `second_brain/docs/2026-07-21_hub_fanin_alphaguard_fb_meta_write_dev_guide_pass164n.md`  
**Scored against hub working defaults:** GOOG→GOOGL **out**; Implement = **builder + tests + docs first** (no parquet / Option B rebuild in first Implement unless Tom overrides)

**Locks (do not reopen):** Tom wants graceful FB→META unify; Yahoo `FB` never for Meta prices; Soft-pin versioning + provenance + fail-closed; Build DoD remains declared MV (post-MV hygiene)

## Call

**READY (Go)** for Implement of the bounded FB→META Soft Adjust — **with soft residuals**.  
**Do not Implement in this stage.** Soft residuals remain and Ready ≠ Implement authorize → Tom should say the authorize phrase below before coding starts.

### Implement readiness

| Track | Score | Why not 10 |
|-------|-------|------------|
| FB→META Soft Adjust (builder + tests + docs first) | **9.1 / 10** | (1) Phase B3 fail-closed is Soft Adjust on top of existing `all sampled rows dropped` `RuntimeError` — Implement must strengthen the META / `fb_meta_v1` message and decide when empty-META after alias is distinguishable from other all-drop cases. (2) Join probe is intentional Soft Adjust (heredoc stub vs `scripts/probe_fb_meta_join.py`) — DoD intent locked, artifact path not copy-paste pinned. (3) Hub working defaults used for GOOG-out + builder-only; Tom has not yet spoken an explicit authorize phrase locking delivery shape in chat. (4) Builder-only path leaves live parquet ticker mix / Option B metrics unchanged until a follow-on regenerate — honesty residual is documented (guide D4/E2), not a design hole. |

**Overall:** **9.1 / 10** · **Go** (authorize phrase still required)

**Not inflated:** Guide is executable (phases A–F, Soft pins, DoD, blast/edges); live code hooks match guide assumptions; no Refine-dev-guide was required to unblock; no code started this stage.

### Alignment (guide ↔ TRAINING_DATA ↔ live code)

| Check | Status |
|-------|--------|
| TRAINING_DATA alias pricing rule + Yahoo FB≠Meta evidence | **Aligned** — rule drafted “when soft-pinned later”; 389 FB rows; 77/86 META same-day close; Yahoo FB = wrong ETF |
| ARCHITECTURE §7.1 “no silent remap” | **Aligned for Ready** — guide treats Soft Adjust as **documented / versioned** training alias; Phase D3 thin §7.1 note is same-delivery docs (not a Ready blocker) |
| Alias not yet coded | **Expected** — `load_filter_dedup_sample` still OOU-drops FB; watches `alias_candidates_oou` for FB/GOOG only |
| `source_row_hash` on raw `stock` | **Aligned** — `source_row_hash(date, stock, headline)` still uses raw stock today |
| `event_id` on post-alias ticker | **Aligned by design** — `event_id_for(ticker, …)` after remap will use META |
| Price path has no FB guard yet | **Expected** — `default_yfinance_closes` / cache accept any ticker string; guide B1 adds reject |
| Existing all-drop fail-closed | **Present** — `dataset_build.py` raises if `not rows` after as-of/label join |
| Test baseline | **Present** — `test_ingest_reports_absent_universe_and_fb_alias_candidate` asserts current (alias-off) honesty; guide C1–C5 update/extend |
| GOOG→GOOGL out | **Aligned** — guide Soft pin + hub default; GOOG remains watch-only |
| Builder+tests+docs first | **Aligned** — guide Phase E2; hub fan-in default |
| Character / MV | **Aligned** — post-MV hygiene; no brokerage/PnL/Guide 09; smoke stays fixture |
| File size headroom | **OK** — ingest 243 / asof 222 / build 226 lines (≤300 prefer) |

### Evidence attached this Ready-check

| Item | Result |
|------|--------|
| Guide status | Write complete — not Implemented; Soft pins `fb_meta_v1`, default alias on, toggle off for honesty tests |
| Ingest today | `BUILDER_VERSION = "0.1.0"`; FB/GOOG watch counts; universe filter drops FB; META absent when no native META |
| Build log today | WARNING “no silent remap” + NOTE OOU rename candidates — Implement A5 must clarify when alias on |
| Fetcher today | No `FB` reject; empty series → row drop / all-drop RuntimeError |
| Universe contract | `TICKER_UNIVERSE` includes `META`, not `FB` |
| FINANCE_HONESTY | Option B lab metrics quoted; builder-only Implement must **not** invent new META coverage claims until regenerate |
| Hub fan-in | Defaults frozen for this Ready: GOOG out; builder+tests+docs first |

### Blast radius / rollback

| Angle | Assessment |
|-------|------------|
| Training ingest only | Alias in `dataset_ingest` — fixtures / RSS / `NewsEvent` still reject raw `FB` → rollback = revert alias commit / default toggle off |
| Wrong-instrument prices | Hard reject `FB` on builder fetch path + unit test → primary poison risk mitigated |
| Stratified sample / `event_id` | FB-origin rows become META identity; parquet not row-comparable to pre-alias → bump `builder_version`; expected |
| Docs honesty | Same-delivery TRAINING_DATA + thin §7.1 + FINANCE_HONESTY note (regenerate deferred) |
| Live Option B metrics | Unchanged under builder-only → no stale metric rewrite required this Implement |
| Over-broad alias | Hard-code FB→META only; C5 asserts GOOG untouched |

### Edge cases (guide covers — verified against code contracts)

1. Native META + FB → both META; dedup after alias  
2. Alias on, zero FB → zero applied count; no error  
3. Alias off → FB OOU + candidate count (honesty)  
4. Empty / missing META series → fail closed (B3 Soft Adjust on existing all-drop)  
5. Non-session FB headline day → as-of drop/shift; probe must not invent closes  
6. Casing `fb` / `Fb` → upper then alias  
7. Fixture/RSS `FB` → still reject (out of scope to accept)  
8. Cursor proxy 403 on yfinance → `run_direct_network.sh` (existing TRAINING_DATA note)

### Refinements still required before Implement?

**None blocking Ready Go.** Soft Implement preferences (not No-Go):

1. **B3 message Soft Adjust:** when alias on and META series empty causes all-drop (or aliased subset cannot join), error text should mention `fb_meta_v1` / META — do not redesign as-of.  
2. **Join probe Soft Adjust:** Implement may add `scripts/probe_fb_meta_join.py` or inline; must never download `FB`; report coverage fraction only.  
3. **Docs honesty for builder-only:** TRAINING_DATA must say coded + “regenerate parquet to refresh live evidence”; do not claim current parquet already has META.  
4. **Optional:** Tom can still override GOOG-in or include-rebuild before authorize — otherwise Implement stays hub defaults.

### Explicit non-claims (this stage)

- No Implement started  
- No parquet rebuild / Option B train  
- No GOOG→GOOGL  
- No MSFT/SPY invention  
- No brokerage / PnL / Guide 09  
- Ready ≠ Implement authorization  

### Open human gates (surface in chat)

#### 1. Authorize Implement under hub defaults?

- **In plain terms:** Ready says Go at 9.1/10 for builder+tests+docs; soft residuals remain → need explicit authorize before coding.  
- **Options:** (A) Authorize builder+tests+docs only · (B) Authorize including parquet+Option B rebuild · (C) Park / request Refine  
- **Recommendation:** **(A)** — matches hub default; proves alias + fail-closed without FinBERT/network coupling.  
- **Reasoning:** Guide Soft pins + tests + docs are enough for a clean first delivery; live META-in-parquet evidence is a follow-on Phase E.  
- **Tradeoffs:** (A) docs must say regenerate later; (B) fuller demo evidence, longer/flakier.  
- **Needs from you:** `Authorize Implement FB→META builder+tests+docs only` (or override to include rebuild / park).

#### 2. GOOG→GOOGL (still open; hub default out)

- **In plain terms:** Keep Alphabet split honesty, or add a second alias now?  
- **Recommendation:** Keep **out** (FB→META only).  
- **Needs from you:** Confirm A (default) or lock B before/with authorize.

### QUALITY_STANDARD §5

Assumptions checked against ingest/build/asof/tests + TRAINING_DATA + §7.1; spoke stayed in Ready slice; blast ≥2 angles; edges planned; numeric score + why not 10; findings in this note + handoff Results; no Implement.

### Stop

Ready Definition of Done Met (**Go 9.1/10**). Wait for Tom authorize before any Implement.
