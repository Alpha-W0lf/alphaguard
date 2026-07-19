# Prioritize — AlphaGuard build doneness reaffirm (pass 163)

**Date:** 2026-07-19  
**Repo:** `alphaguard`  
**Mode:** spoke  
**Stage:** Prioritize next work  
**Hub:** pass 163 — idle only if declared VISION build MV Met; interview prep separate  
**Spoke:** `0a88890e-8c9d-4101-b019-8754f212607d`

## Declare

Reaffirm whether AlphaGuard still has residual **build** work toward **100% declared Minimum Viable (v1 build Done)** — not interview fluency, not production risk model, not inventing Guide 09.

## Evidence opened

- `docs/VISION.md` § Minimum Viable (v1 build Done) — all six boxes `[x]`  
- `docs/VISION.md` § Interview prep — both boxes `[ ]` (human-only; not build %)  
- `docs/VISION.md` § Future Enhancements — post-v1 optional (Streamlit, hold-out eval, fine-tune) — **out of declared MV**  
- `AGENTS.md` — Build MV Met on guides 01–08; CI + PolyForm-NC polish; no agent-on-consume  
- Inventory `docs/2026-07-17_post_guide06_next_slice_inventory_context_summary.md` — A/A2/G/H Done; D/E/C open as **post-MV** candidates  
- Local runnable: `GETTING_STARTED.md` / `Makefile` `make smoke` (fixture / Kafka-down)  
- Polish landed: `.github/workflows/ci.yml`, root `LICENSE` (PolyForm-NC)  
- `gh api`: repo still **private**; license `NOASSERTION` (expected for PolyForm)

## Declared build MV checklist (VISION)

| Gate | Status |
|------|--------|
| Compose Kafka + Qdrant documented | **[x]** |
| 05a training-events builder | **[x]** |
| 05b Option B train + metrics | **[x]** (lab; smoke stays fixture) |
| Replay fixture headline → local envelope (+ 07/08 fail-open when configured) | **[x]** |
| README polish (diagram / stack / limitations) | **[x]** |
| INTERVIEW.md ≥15 gotchas | **[x]** |

**Build % (declared MV only):** **~100%** — all VISION Minimum Viable boxes checked.

**Local runnable + documented smoke:** **Yes** — `make smoke` / GETTING_STARTED Kafka-down fixture path.

## Residual list (toward declared MV)

*(empty)* — no unchecked VISION Minimum Viable build gates.

### Explicitly not residuals for declared MV

| Item | Why excluded |
|------|----------------|
| Interview-prep walkthrough / hand-coding | VISION marks **not** build blockers; human-only |
| Agent-on-consume | Inventory **D** — large post-MV; would need new Prioritize + Guide invent |
| Live-Ollama eval schema-pass rates | Inventory **E** — honesty already “not live-Ollama rates” |
| U4 FB→META / train hygiene | Inventory **C** — thin hygiene; not an MV box |
| Guide 06 E3 live Yahoo | Optional ops proof; Yahoo flake already disclosed |
| D3 live LangSmith/Phoenix probes | Soft residual; fail-open already Met |
| Future Enhancements (Streamlit, etc.) | Post-v1 optional |

### Soft deploy note (not Soft Adjust code)

| Item | Note |
|------|------|
| GitHub repo still **private** | Packaging + CI + LICENSE Met; “make public” is a **Tom ops lock**, not a code Implement. Does **not** uncheck VISION MV boxes (those require polish content, which shipped). |

## Ordered recommendation

1. **Idle** AlphaGuard for hub build-doneness tracking — declared MV Met; local smoke documented.  
2. **Do not** start Write/Implement for agent-on-consume / Guide 09 without a new hub Prioritize that **expands** declared MV.  
3. Optional (human-only): flip repo visibility public when Tom wants stranger-clone optics; optional Interview-prep rehearsal — neither is agent build work.

## Overlooked / doc conflicts

- None that invalidate idle: VISION Status and AGENTS both say Build MV Met; inventory Soft residuals are post-MV.  
- Wording “not v1 Done” / “not portfolio-complete” in README still means **not production / not interview fluency** — does **not** reopen declared MV boxes.

## Soft Adjust?

**None** in-scope for this Prioritize. No small Soft Adjust that closes a declared MV gap (there is no gap). Making the GitHub repo public is ops, not Soft Adjust Implement.

## Human decision (only if Tom wants more build)

- **Plain title:** Expand AlphaGuard declared MV beyond guides 01–08 + polish?
  - In plain terms: Should the hub invent a next build slice (e.g. agent-on-consume), or keep AG idle?
  - Options: **A** Idle (reaffirm) · **B** New Prioritize for agent-on-consume / Guide 09 · **C** Ops-only: make GitHub public
  - Recommendation: **A**
  - Reasoning: Declared VISION MV is fully checked; remaining inventory items are post-v1 or interview. Hub asked for build doneness only.
  - Tradeoffs: A frees spoke capacity. B grows portfolio capability but reopens “one more feature” spiral. C improves stranger-clone optics without new code.

## Honest call

| Question | Answer |
|----------|--------|
| Declared v1 build MV Met? | **Yes** |
| Local runnable + documented smoke? | **Yes** |
| Residual build gates in VISION MV? | **None** |
| idle_ok? | **yes** |
| Next Write/Implement? | **No** — idle unless Tom expands MV |

## QUALITY §5

- [x] Ordered recommendation with why  
- [x] Overlooked / non-residuals flagged  
- [x] Human decision surfaced with recommendation + tradeoffs  
- [x] No Implement this stage  
