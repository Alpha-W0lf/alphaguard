# Dev Guide — Thin polish: PolyForm Noncommercial LICENSE packaging

**Date:** 2026-07-18  
**Repo:** `alphaguard`  
**Work item:** Thin polish — root **PolyForm Noncommercial License 1.0.0** `LICENSE` + honesty surfaces  
**Stage that authored this:** Write-dev-guide (pass 155); Ready-check (9.2); Implement (pass 155)  
**Status:** **Implement Met** — ready for Review; LICENSE + honesty surfaces landed; **do not Align in Implement**  
**Justify thin guide:** One root legal file + five honesty surfaces; Mechanic Guide 10a prior art complete; hub A/A/A locks already closed Gather open decisions.

**Context SSOT:** `alphaguard/docs/2026-07-18_thin_polish_polyform_nc_license_context_summary.md`  
**Write handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_write_polyform_nc_pass155_handoff.md`  
**Gather handoff:** `second_brain/docs/2026-07-18_spoke_alphaguard_gather_polyform_nc_pass155_handoff.md`  
**Decision note:** `second_brain/docs/2026-07-18_license_polyform_nc_decision_note.md`  
**Prior art:** `mechanic_rag` Guide 10a (Align Met)  
**Prerequisite:** Build MV Met (guides 01–08); CI + ARCH polish Align Met (`6e65e9b`). Default smoke still fixture.

**Human locks (pass 155 — do not reopen):**

| Lock | Value |
|------|--------|
| Stage shape | Thin Write then Ready — **no Implement** in Write/Ready stages |
| License | **PolyForm Noncommercial License 1.0.0** (SPDX `PolyForm-Noncommercial-1.0.0`) — **not** MIT, **not** OSI open source, **not** pure ARR-only |
| Copyright / Required Notice | `Copyright (c) 2026 Tom Chacko` |
| Honesty surfaces | **README + VISION + GETTING_STARTED + INTERVIEW + AGENTS** |
| PUBLIC_FLIP checklist | **Forbidden** — do not invent for AlphaGuard |
| Scope | LICENSE + thin honesty only — **no** agent-on-consume / feature Guide 09 invent |
| Interview-prep VISION boxes | **Human-only** — do not invent ticks |
| `pyproject.toml` license field | **Out of Met** (match Mechanic omission; GitHub may show Other/NOASSERTION) |

---

## Objective

Land root **PolyForm Noncommercial 1.0.0** so clone reviewers know reuse rights: non-commercial OK; commercial rights reserved; portfolio honesty matches Mechanic.

1. Create repo-root `LICENSE` with **verbatim** PolyForm-NC 1.0.0 text + Required Notice.  
2. Update honesty surfaces (locked set) with **source-available / non-commercial** language.  
3. **Stop.** Do not invent public-flip checklist, agent-on-consume, or feature Guide 09.

**Success signal (after Implement):** `test -f LICENSE` green; title line is PolyForm Noncommercial License 1.0.0; greps find source-available honesty on all five surfaces; no MIT/OSI-open-source positive license claims; Interview-prep boxes still unchecked.

---

## Learning notes (interview-portable)

1. **Source-available ≠ open source** — Non-commercial licenses allow public GitHub + learning forks while reserving commercial rights; do not badge as OSI open source.  
2. **License text fidelity** — README may paraphrase honesty; the `LICENSE` body must be official verbatim text.  
3. **GitHub license API** — PolyForm often shows as `Other` / `NOASSERTION`; that is expected metadata, not a Soft Adjust to MIT for a green badge.

---

## References (paths only)

- `alphaguard/docs/2026-07-18_thin_polish_polyform_nc_license_context_summary.md`
- `mechanic_rag/LICENSE` (shipped body + Required Notice pattern)
- `mechanic_rag/docs/dev_guides/2026-07-18_dev_guide_10a_polyform_nc_license_packaging.md`
- `mechanic_rag/README.md` / `GETTING_STARTED.md` / `INTERVIEW.md` (honesty vocabulary)
- `second_brain/docs/2026-07-18_license_polyform_nc_decision_note.md`
- Official: https://polyformproject.org/licenses/noncommercial/1.0.0  
- SPDX: `PolyForm-Noncommercial-1.0.0`  
- Canonical markdown (optional): https://github.com/polyformproject/polyform-licenses/blob/1.0.0/PolyForm-Noncommercial-1.0.0.md  
- `alphaguard/README.md` · `docs/VISION.md` · `GETTING_STARTED.md` · `INTERVIEW.md` · `AGENTS.md`  
- `alphaguard/docs/dev_guides/2026-07-13_dev_guide_02_interview_packaging.md` (LICENSE deferred — now this polish)  
- Do **not** use `ai-knowledge-base-public/LICENSE` (MIT) as the body

---

## Architecture constraints (binding)

1. **LICENSE + thin docs only.** No pipeline, CI, Kafka, Ollama, agents, eval, Option B, or RAG code.  
2. **PolyForm-NC 1.0.0 only.** Do not substitute MIT, Apache-2.0, ARR-only, or invent custom terms.  
3. **Honesty set locked.** Touch README, VISION, GETTING_STARTED, INTERVIEW, AGENTS. Do **not** invent `docs/PUBLIC_FLIP_CHECKLIST.md`. ARCHITECTURE header one-liner is **optional Soft Adjust** only if grep honesty needs it — not required by hub lock.  
4. **Copyright pin:** `Required Notice: Copyright (c) 2026 Tom Chacko` — do not invent a second conflicting copyright block.  
5. **Honesty language:** Must **not** call the repo OSI open source or MIT after this guide. Prefer “source-available / non-commercial.” Commercial use → contact copyright holder.  
6. **TRAINING_DATA.md** stays about Kaggle/training-data license — do not conflate with repo LICENSE.  
7. **Interview-prep VISION boxes** stay unchecked.  
8. **No** agent-on-consume / feature Guide 09 invent.  
9. Prefer ≤300 lines for any new guide-adjacent notes; LICENSE body length is fixed by official text (~75 lines).

---

## Soft pins (binding for Implement)

| Pin | Locked default |
|-----|----------------|
| File path | Repo root `LICENSE` (exact name; not `LICENSE.md`) |
| License family | **PolyForm Noncommercial License 1.0.0** |
| SPDX id | `PolyForm-Noncommercial-1.0.0` |
| Body source | Prefer **byte-copy** `mechanic_rag/LICENSE` after `head`/`diff` spot-check vs official PolyForm-NC 1.0.0 (polyformproject.org or polyform-licenses tag `1.0.0`) — **verbatim**, not paraphrased |
| Required Notice | `Required Notice: Copyright (c) 2026 Tom Chacko` |
| README | Status (or top) line + Docs link to `LICENSE`; state source-available / non-commercial; commercial → contact; not OSI / not MIT |
| VISION | Status and/or Last Updated prose: LICENSE Met (PolyForm-NC); Interview-prep boxes unchanged `[ ]` |
| GETTING_STARTED | Thin intro one-liner (Mechanic pattern OK) |
| INTERVIEW | Thin intro one-liner; optional FAQ bullet only if needed — keep thin |
| AGENTS | One short honesty sentence in lead paragraph or Docs SSOT section |
| Forbidden positive claims | “open source” (OSI sense) as the repo license; “MIT” as current license; “public flip ready”; “v1 Done”; “portfolio complete” from this polish alone |
| `pyproject.toml` | Do **not** add `[project].license` in this guide |

### Suggested honesty snippets (Implement may Soft Adjust wording, not meaning)

**README Status-ish line:**

```text
**License:** PolyForm Noncommercial 1.0.0 — **source-available / non-commercial** (not OSI open source; not MIT). Commercial use → contact copyright holder. See [`LICENSE`](LICENSE).
```

**VISION Last Updated / Status addendum:**

```text
LICENSE: PolyForm-NC 1.0.0 (source-available / non-commercial); Interview-prep boxes still separate / unchecked
```

---

## Acceptance criteria (Implement must meet)

- [x] Root `LICENSE` exists with **verbatim** PolyForm Noncommercial 1.0.0 text + pinned Required Notice  
- [x] README / VISION / GETTING_STARTED / INTERVIEW / AGENTS: LICENSE present; **source-available / non-commercial** honesty; commercial contact; no MIT/OSI-open-source mislabel  
- [x] No `docs/PUBLIC_FLIP_CHECKLIST.md` created  
- [x] Interview-prep VISION boxes still unchecked  
- [x] No pipeline/code/CI changes; no agent-on-consume  
- [x] Verification commands pass  

---

## Ordered step checklist

### Phase A — Anchor

- [x] **A1.** Confirm `test ! -f LICENSE` (or stop if unexpected LICENSE exists — escalate Tom).  
- [x] **A2.** Confirm hub locks: PolyForm-NC + Tom Chacko 2026 + honesty set B + no PUBLIC_FLIP invent.  
- [x] **A3.** Confirm VISION Interview-prep boxes are `[ ]` before edits.  
- [x] **A4.** Fetch/spot-check body: `mechanic_rag/LICENSE` vs official PolyForm-NC 1.0.0 (title + Required Notice line). Prefer copy Mechanic LICENSE if match.

### Phase B — Add PolyForm-NC LICENSE

- [x] **B1.** Create root `LICENSE` with **verbatim** PolyForm-NC 1.0.0 body; include `Required Notice: Copyright (c) 2026 Tom Chacko`.  
- [x] **B2.** `test -f LICENSE` and `head -n 5 LICENSE` — expect PolyForm Noncommercial License 1.0.0 (not MIT).

### Phase C — Honesty surfaces (locked set)

- [x] **C1.** README — License line + Docs link to `LICENSE`; source-available / non-commercial; commercial contact.  
- [x] **C2.** VISION — Status and/or Last Updated honesty; Interview-prep boxes **unchanged** `[ ]`.  
- [x] **C3.** GETTING_STARTED — thin intro License one-liner.  
- [x] **C4.** INTERVIEW — thin intro License one-liner.  
- [x] **C5.** AGENTS — one honesty sentence (lead or Docs SSOT).  
- [x] **C6.** Grep honesty (below): must find PolyForm / source-available; must **not** find MIT-as-current-license or OSI-open-source-as-license claims; must **not** create PUBLIC_FLIP checklist.

### Phase D — Stop

- [x] **D1.** No code/CI/train/eval changes; no agent-on-consume; no PUBLIC_FLIP invent.  
- [x] **D2.** Stop for Review (after Ready-check → Implement authorize). **Do not Align in Implement.**

---

## Verification / Definition of Done

```bash
# From alphaguard/
test -f LICENSE
head -n 5 LICENSE   # PolyForm Noncommercial License 1.0.0; Required Notice Tom Chacko

rg -n 'LICENSE|PolyForm|Noncommercial|source-available|MIT|open source' \
  LICENSE README.md docs/VISION.md GETTING_STARTED.md INTERVIEW.md AGENTS.md

# Must find: PolyForm-NC LICENSE; source-available / non-commercial on honesty surfaces
# Must NOT find as positive claims: MIT as current repo license; OSI open source as license;
#   public flip ready; v1 Done from this polish alone

test ! -f docs/PUBLIC_FLIP_CHECKLIST.md

# Interview-prep boxes still unchecked (VISION) — adjust rg to actual checkbox wording
rg -n 'Interview prep|walkthrough|hand-coding' docs/VISION.md | head
```

**DoD (Implement):** Root PolyForm-NC `LICENSE` present (verbatim + Required Notice); five honesty surfaces updated; no PUBLIC_FLIP invent; Interview-prep unchecked; no code/agent-on-consume.

**DoD (this Write):** Executable thin guide with locks, phases, DoD, blast, edges; **no** LICENSE file created; **no** Implement.

---

## Blast radius and risks

| Risk | Angle | Mitigation |
|------|-------|------------|
| Mislabel as OSI open source / MIT | Recruiter / legal honesty | Soft pins + C6 grep |
| Paraphrased LICENSE body | Legal fidelity | Byte-copy Mechanic / official only |
| Wrong copyright | Legal | Locked Tom Chacko 2026 |
| Scope into agent-on-consume / Guide 09 | Feature creep | Phase D hard stop |
| Invent PUBLIC_FLIP checklist | Process invent | Hub lock; verification `test ! -f` |
| Conflate TRAINING_DATA license | Docs honesty | Leave TRAINING_DATA.md alone |
| Soft Adjust to MIT for GitHub badge | Metadata temptation | Explicit forbid |

**Blast radius:** `LICENSE`, `README.md`, `docs/VISION.md`, `GETTING_STARTED.md`, `INTERVIEW.md`, `AGENTS.md`. **Not** pipeline/code/tests/CI.

### Rollback

Delete `LICENSE`; revert honesty doc commits.

---

## Edge-case handling

| Case | Behavior |
|------|----------|
| `LICENSE` already exists (e.g. accidental MIT) | Stop; compare to PolyForm-NC pin; escalate Tom |
| Temptation to badge “Open Source” | **Hard fail** — use source-available / non-commercial |
| Temptation to invent PUBLIC_FLIP checklist | **Hard fail** — out of Met |
| Temptation to copy AI KB MIT | **Hard fail** |
| Temptation to tick Interview-prep boxes | **Hard fail** |
| GitHub shows Other / NOASSERTION after push | Expected — do not Soft Adjust to MIT |
| Repo remains private | Still land LICENSE; private ≠ skip license |

---

## Out of scope (stop list)

- Implement / create LICENSE in this Write stage  
- Agent-on-consume / feature Guide 09  
- PUBLIC_FLIP checklist invent  
- `pyproject.toml` license metadata  
- AI KB MIT retarget  
- Making GitHub repo public  
- Mechanic / Vehicle / AI KB edits from this spoke  

---

## Honest readiness

- **Write / Ready / Implement DoD:** **Met** this pass.  
- **Next:** Review implementation (hub authorize) — **do not Align here**.  
- **LICENSE:** Root PolyForm-NC present (byte-match Mechanic + Required Notice Tom Chacko).  
- **Will not** invent agent-on-consume or feature Guide 09.

## QUALITY self-check (§5)

- [x] Locks closed; soft pins executable  
- [x] Steps + DoD + blast + edges present  
- [x] No code / no LICENSE file in Write  
- [x] Thin guide justified; Mechanic prior art cited  
- [x] Spoke stayed in LICENSE polish slice  
