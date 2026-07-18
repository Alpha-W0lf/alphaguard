# Context: Thin polish — root PolyForm Noncommercial 1.0.0 LICENSE

**Date:** 2026-07-18 · **Updated:** 2026-07-18 (Align PolyForm-NC LICENSE pass 155)  
**Repos:** `alphaguard`  
**Status:** **Align Met / slice closed** — root PolyForm-NC LICENSE + honesty Met  
**Mode last used:** spoke (Align pass 155)  
**Stage:** Align-docs (complete)  
**Write guide:** `docs/dev_guides/2026-07-18_dev_guide_thin_polish_polyform_nc_license.md` (Aligned)  
**Implement:** `c7c2e00` · Review: `a4f488d` · Align: this pass  
**Role lens:** Portfolio packaging / legal honesty (source-available) — not product features  
**Handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_align_polyform_nc_pass155_handoff.md`  
**Prior slice:** CI + ARCH polish Align Met (`6e65e9b`)  
**Hub lean:** Prefer **PolyForm Noncommercial 1.0.0** (match Mechanic Guide 10a) — **locked and shipped**  
**Decision note:** `second_brain/docs/2026-07-18_license_polyform_nc_decision_note.md`

## Outcome (Align pass 155 — supersedes Gather “LICENSE absent” prose)

| Item | Reality after thin polish |
|------|---------------------------|
| Root `LICENSE` | PolyForm Noncommercial 1.0.0 + Required Notice Tom Chacko — Met (`c7c2e00`; byte-match Mechanic) |
| Honesty surfaces | README + VISION + GETTING_STARTED + INTERVIEW + AGENTS — source-available / non-commercial; commercial contact Soft Align |
| PUBLIC_FLIP checklist | **Not** invented |
| Interview-prep VISION boxes | Still **unchecked** |
| Guide 09 / agent-on-consume | **Not** invented |

## Problem (historical Gather — pass 155)

AlphaGuard **build MV is Met** (guides 01–08 + CI/ARCH polish). Root **`LICENSE` was absent**. Closed by Implement `c7c2e00` / Align pass 155.

This was **thin packaging polish**, not a feature Guide 09.

Without a root LICENSE, clone reviewers / future public flip cannot tell reuse rights; default GitHub `license: null` on the (currently **private**) AlphaGuard remote reinforces the gap.

This is **thin packaging polish**, not a feature Guide 09 / agent-on-consume.

## Acceptance criteria

- [ ] Root `LICENSE` exists with **verbatim** PolyForm Noncommercial License 1.0.0 text (official source; not paraphrased)  
- [ ] Required notice / copyright pinned consistently (Mechanic pattern: `Required Notice: Copyright (c) 2026 Tom Chacko`)  
- [ ] Thin honesty surfaces state **source-available / non-commercial** — **not** OSI open source, **not** MIT, **not** pure ARR-only story  
- [ ] Commercial use → contact copyright holder (one clear line)  
- [ ] No agent-on-consume / no feature Guide 09 invent  
- [ ] Interview-prep VISION boxes remain unchecked  
- [ ] Do **not** invent Mechanic-style `PUBLIC_FLIP_CHECKLIST` for AlphaGuard in this slice (AG has none today)  
- [ ] Training-data Kaggle/CC0 notes in `docs/TRAINING_DATA.md` stay separate from **repo** LICENSE

## In scope

- Create root `LICENSE` (exact name; not `LICENSE.md`) from official PolyForm-NC 1.0.0  
- Thin honesty: README (status + Docs link), VISION Status/Last Updated prose, optional one-liners in GETTING_STARTED / INTERVIEW / AGENTS / ARCHITECTURE header if needed for grep honesty  
- Cite Mechanic Guide 10a as copy pattern (body + honesty vocabulary)

## Out of scope

- Implement in this Gather stage  
- Agent-on-consume / live consume / Guide 09 feature invent  
- Changing CI, Kafka, Ollama, Phoenix/LangSmith adapters, eval goldens, Option B train  
- Inventing `docs/PUBLIC_FLIP_CHECKLIST.md` or claiming “public flip ready” / “v1 Done”  
- Retargeting AI KB MIT LICENSE  
- Soft Adjusting training-data license text  
- Making the GitHub repo public (separate Tom lock)

## Prior art (paths only)

- `mechanic_rag/LICENSE` — shipped PolyForm-NC 1.0.0 (75 lines; `Required Notice: Copyright (c) 2026 Tom Chacko`)  
- `mechanic_rag/docs/dev_guides/2026-07-18_dev_guide_10a_polyform_nc_license_packaging.md` — Implement checklist + Soft Adjust MIT→PolyForm-NC history  
- `mechanic_rag/docs/2026-07-18_guide10a_align_polyform_nc_pass155_note.md` — Align Met  
- `mechanic_rag/README.md` — Status line + License bullet (source-available / non-commercial)  
- `second_brain/docs/2026-07-18_license_polyform_nc_decision_note.md` — portfolio lock rationale  
- Official: https://polyformproject.org/licenses/noncommercial/1.0.0  
- SPDX: `PolyForm-Noncommercial-1.0.0`  
- Canonical markdown (optional): https://github.com/polyformproject/polyform-licenses/blob/1.0.0/PolyForm-Noncommercial-1.0.0.md  
- `alphaguard/docs/dev_guides/2026-07-13_dev_guide_02_interview_packaging.md` — LICENSE deferred out of Guide 02 DoD  
- Do **not** copy `ai-knowledge-base-public/LICENSE` (MIT) as the AlphaGuard body

## Soft pins (hub lean — confirm in Write; do not reopen casually)

| Pin | Default |
|-----|---------|
| License family | **PolyForm Noncommercial License 1.0.0** (SPDX `PolyForm-Noncommercial-1.0.0`) |
| File path | Repo root `LICENSE` |
| Body | Verbatim official PolyForm-NC 1.0.0 (prefer copy from `mechanic_rag/LICENSE` after spot-check vs polyformproject.org) |
| Copyright / Required Notice | `Copyright (c) 2026 Tom Chacko` (match Mechanic unless Tom amends) |
| Honesty label | **Source-available / non-commercial** — not OSI open source; not MIT |
| Scope split | LICENSE + thin docs only — **P1 packaging**; no public-flip invent |
| `pyproject.toml` `[project].license` | **Out** unless Write explicitly adds (Mechanic omitted; GitHub may show `Other` / NOASSERTION — acceptable) |

## Risks and blast radius

| Risk | Angle | Mitigation |
|------|-------|------------|
| Mislabel as OSI “open source” / MIT | Recruiter / legal honesty | Soft pins + grep after Implement |
| Paraphrased LICENSE body | Legal fidelity | Verbatim only; prefer mechanic_rag/`LICENSE` byte-match after URL check |
| Scope into agent-on-consume | Feature creep | Hard stop; polish only |
| Confuse training-data license with repo LICENSE | Docs honesty | Keep TRAINING_DATA.md separate; README clarifies repo license |
| Claim public flip / v1 Done from LICENSE alone | Marketing | No PUBLIC_FLIP invent; Interview-prep boxes untouched |
| Wrong copyright string | Legal | Pin Tom Chacko 2026; escalate if Tom wants different |

**Blast radius:** `LICENSE` + thin honesty docs (README / VISION ± GETTING_STARTED / INTERVIEW / AGENTS / ARCHITECTURE header). **Not** pipeline/code/tests.

### Rollback

Delete `LICENSE`; revert honesty doc commits.

## Edge cases

| Case | Behavior |
|------|----------|
| `LICENSE` already exists unexpectedly | Stop; compare to PolyForm-NC pin; escalate Tom |
| Temptation to badge “Open Source” on GitHub topic | **Hard fail** — use source-available / non-commercial |
| Temptation to invent AG `PUBLIC_FLIP_CHECKLIST` | Out of Met this slice |
| Temptation to copy AI KB MIT | Forbidden |
| Repo currently private (`gh` license null) | Still add LICENSE for honesty + future public; private ≠ no license |
| GitHub SPDX may show “Other” / NOASSERTION | Expected for PolyForm; do not Soft Adjust to MIT for badge |

## Unknowns (must resolve or escalate)

| Unknown | How to resolve | Blocking? |
|---------|----------------|-----------|
| Exact copyright string if Tom prefers different legal name | Confirm in Write soft pins / Tom chat | Soft — default Mechanic string |
| Whether ARCHITECTURE header one-liner is required vs README+VISION enough | Write picks thinnest honest set | No |
| GitHub “About” license UI after push | Observe after Implement; no MIT Soft Adjust for badge | No |

## Recommended approach

1. Thin **Write-dev-guide** (≤1 short guide) mirroring Mechanic 10a Phases A–D but **without** PUBLIC_FLIP gate edits.  
2. Soft pins: PolyForm-NC verbatim + Tom Chacko 2026 notice + source-available honesty.  
3. Implement later: create `LICENSE` (copy verified Mechanic body), update README Status/Docs + VISION Last Updated, thin optional surfaces.  
4. Stop for Review → Align. **No** agent-on-consume.

**Justify thin Write:** One new file + few honesty lines; Gather already locks family via hub lean + Mechanic prior art. Still want an executable checklist (body source, grep DoD, stop list).

## Open decisions (human)

- **Plain title:** Next stage shape for this LICENSE polish?
  - In plain terms: Write a short guide, or jump Ready-check from this context?
  - Options: **A** Thin Write-dev-guide then Ready-check · **B** Skip Write; Ready-check from this context alone · **C** Implement immediately after Gather
  - Recommendation: **A**
  - Reasoning: Workflow OS wants an executable checklist (verbatim body, honesty grep, stop list). Change is small but legally sensitive — Write is cheap insurance vs C.
  - Tradeoffs: A adds one short stage. B faster but weaker handoff. C skips Ready gate.

- **Plain title:** Copyright / Required Notice string?
  - In plain terms: Whose name goes on the PolyForm Required Notice line?
  - Options: **A** `Copyright (c) 2026 Tom Chacko` (match Mechanic) · **B** Different legal name/year Tom specifies
  - Recommendation: **A**
  - Reasoning: Portfolio consistency; Mechanic already shipped this notice; hub PolyForm decision note assumes Tom as licensor.
  - Tradeoffs: A is zero new legal naming work. B needs Tom text before Implement.

- **Plain title:** Honesty surface set (minimum)?
  - In plain terms: Which docs must mention the license after Implement?
  - Options: **A** README + VISION Status (minimum) · **B** A + GETTING_STARTED + INTERVIEW + AGENTS one-liners · **C** B + invent PUBLIC_FLIP checklist
  - Recommendation: **B**
  - Reasoning: Mechanic used multi-surface honesty so greps cannot miss; AG has no public-flip checklist today — inventing one is scope creep (C).
  - Tradeoffs: B is a few extra lines. A risks INTERVIEW silence. C invents process AG never had.

## Learning notes (interview-portable)

1. **Source-available ≠ open source** — Non-commercial licenses allow public GitHub + learning forks while reserving commercial rights; recruiters hear “open source” as OSI — do not badge PolyForm-NC as OSI open source.  
2. **SPDX / GitHub license API** — Non-OSI licenses often show as `Other` / `NOASSERTION` on GitHub; that is metadata, not a reason to switch to MIT for a green badge.  
3. **License text fidelity** — The `LICENSE` file is a legal instrument; paraphrase in README is OK for honesty, paraphrase **as** the LICENSE body is not.

## Evidence opened this pass

- Handoff `…_gather_polyform_nc_pass155_handoff.md`; hub lean PolyForm-NC  
- `test ! -f LICENSE` in alphaguard → absent  
- `mechanic_rag/LICENSE` head + 75 lines; Guide 10a + Align note; README Status license line  
- `second_brain/docs/2026-07-18_license_polyform_nc_decision_note.md`  
- alphaguard README / VISION / GETTING_STARTED / INTERVIEW / AGENTS / pyproject — **no** repo LICENSE claim; no `PUBLIC_FLIP_CHECKLIST.md`  
- Guide 02 deferred LICENSE out of DoD  
- `gh api` AlphaGuard: `private: true`, `license: null`; Mechanic: `license.spdx_id: NOASSERTION` (Other)  
- Prior CI/ARCH Align `6e65e9b` closed; polish lane continues

## Honest readiness

- **Gather → Align:** **Met** — slice closed.  
- **Will not** invent agent-on-consume or feature Guide 09.  
- **Will not** invent PUBLIC_FLIP checklist.

## QUALITY self-check (§5)

- [x] Assumptions listed as soft pins / open decisions  
- [x] Edge cases + blast radius (≥2 angles: mislabel OSI/MIT; paraphrased body)  
- [x] Findings written to this artifact + handoff Results  
- [x] Spoke stayed in thin LICENSE polish; no Implement  
- [x] Open decisions surfaced with recommendation + reasoning + tradeoffs  
