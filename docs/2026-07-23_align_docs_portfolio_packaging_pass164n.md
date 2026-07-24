# Align docs — AlphaGuard portfolio packaging (pass 164n)

**Date:** 2026-07-23  
**Mode / stage:** hub · Align docs (docs-only)  
**Locks:** `second_brain/docs/2026-07-23_hub_locks_align_and_write_pass164n.md`  
**Critical review:** `docs/2026-07-23_critical_review_portfolio_packaging_readme_pass164n.md`

## Done this pass

| Remediation | Change |
|-------------|--------|
| P0-2 metric integrity | README Option B example → post-alias train F1 ≈0.693, **test F1 ≈0.087**, **3 positives**; points at `FINANCE_HONESTY.md`; labels 0.0/2 as historical |
| P1 early honesty | README **Evidence and limits** callout after status |
| P1 VISION LLMOps | Share / finish-line / sharing table / locked Observability now say **local run summary mandatory**; LangSmith/Phoenix optional when configured |
| P1 screenshot age | `docs/assets/README.md` provenance note: 2026-07-13 fixture evidence only |
| P0-1 visibility | Tom locked **public**; `gh repo edit --visibility public --accept-visibility-change-consequences` → **PUBLIC** (hub verified `isPrivate:false`, unauth HTTP **200**) |

## Explicitly not done

- Screenshot refresh from a current smoke (needs `uv sync` + Ollama smoke)
- Guide 09 / feature code
- Commit of Align edits (Tom must authorize commit if desired)

## Verification

- Grep: README Limitations no longer presents stale 0.0 as current
- `FINANCE_HONESTY.md` / `TRAINING_DATA.md` unchanged as SSOT (already correct)
- Hub confirms `origin` = `Alpha-W0lf/alphaguard.git`
- Visibility: **Met** — `Alpha-W0lf/alphaguard` PUBLIC; unauthenticated `GET https://github.com/Alpha-W0lf/alphaguard` → 200
- CI badge added to README (points at real Actions workflow)
