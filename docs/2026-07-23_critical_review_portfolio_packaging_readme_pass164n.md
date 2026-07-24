# Critical review — AlphaGuard portfolio packaging (README-first)

**Date:** 2026-07-23  
**Mode / stage:** Workflow OS spoke · Critical review only  
**Scope:** Cold hiring-manager / GitHub-reader packaging: `README.md`, `GETTING_STARTED.md`, `INTERVIEW.md`, `docs/VISION.md`, `docs/FINANCE_HONESTY.md`, `docs/WALKTHROUGH_10MIN.md`, license, CI, committed screenshots, and repository exposure.  
**Role lenses:** Senior AI engineer (claim-to-evidence), ML engineer (metric integrity), and quant/risk reviewer (no investment-performance overclaim).

## Verdict

The written package is unusually candid about the project boundary: it consistently presents a local, replay-first interview lab rather than a trading product, and it clearly separates fixture plumbing from the Option B laboratory model. It is **not ready to use as a cold public portfolio link**, however: the local checkout points to an unrelated repository, the intended AlphaGuard GitHub repository is private, and the README publishes Option B metrics that conflict with the finance-honesty source.

The bounded build may remain “complete” under its locked local-plus-continuous-integration finish line. This review does **not** reopen that build Definition of Done; it finds portfolio-distribution and documentation-integrity failures that must be resolved before presenting the repository to strangers.

## Evidence reviewed and verification boundary

| Evidence | What it establishes |
|---|---|
| `README.md` lines 3–7, 74–84, 98–111 | Clear opening, architecture, license framing, screenshots, limitations, and the published Option B metric example. |
| `GETTING_STARTED.md` lines 1–100 | A clean-clone replay path, explicit optional Kafka/RSS paths, and no fabricated hosted-service promise. |
| `INTERVIEW.md` lines 1–88 and `docs/WALKTHROUGH_10MIN.md` | Useful technical-defense material; rehearsal remains explicitly human-owned and uncompleted. |
| `docs/FINANCE_HONESTY.md` lines 1–37 and `docs/TRAINING_DATA.md` lines 127–148 | The current local Option B example is `test F1 ≈0.087` with three positive test cases, explicitly weak/noisy. |
| `docs/VISION.md` lines 3–7, 45–62, 115–146, 261–271, 297–315 | Current bounded-MV framing is mostly sound, but legacy “public repo / trace screenshots required” wording remains. |
| `.github/workflows/ci.yml` lines 1–24 and `tests/test_eval_stubs.py` lines 25–52 | Default CI runs `uv run pytest -q`; the evaluated golden-test floor is at least 21 cases. |
| `docs/assets/README.md` lines 1–17 | Committed images are honestly local-envelope evidence, but their source run is 2026-07-13. |
| Live local Git metadata (2026-07-23) | `origin` fetch/push is `Alpha-W0lf/polk_county_vehicle_title_and_registration.git`, not `Alpha-W0lf/alphaguard.git`; recent local history is also from the unrelated Polk County project. |
| GitHub authenticated repository lookup (2026-07-23) | `Alpha-W0lf/alphaguard` exists, has `main`, was pushed 2026-07-21, and is **private**. |

`uv run pytest -q` was attempted as a packaging-verification check but could not start because this checkout has no installed `pytest` executable. This review therefore does **not** claim a fresh local test pass; its CI/test statements are documentation and configuration evidence only.

## Ranked findings

### P0 — Must resolve before sharing this as a cold portfolio repository

#### P0-1 — The local checkout’s Git remote is an unrelated repository, while the actual AlphaGuard repository is private

**Evidence**

- The README and VISION describe a public-GitHub sharing strategy (`README.md` line 91; `docs/VISION.md` lines 53 and 265–271), and `VISION.md` locks repository visibility to “Public” (line 301).
- Local `origin` is `https://github.com/Alpha-W0lf/polk_county_vehicle_title_and_registration.git` for both fetch and push. The local recent commits are Polk County documents, not AlphaGuard work.
- The authenticated GitHub lookup finds `Alpha-W0lf/alphaguard`, but reports `private: true`.

**Why this is a portfolio blocker**

There is no safe path from this working tree to the intended public portfolio repository. A stranger cannot inspect the intended source, and an ordinary `git push` from this checkout risks writing AlphaGuard work into an unrelated repository. The package’s “public repo” language is therefore not just aspirational; it is presently contradicted by the delivery path.

**Smallest remediation**

1. **Stop all normal pushes from this checkout** until repository identity is deliberately repaired.
2. Tom should verify which checkout is authoritative and then either reclone `Alpha-W0lf/alphaguard` or explicitly repoint the remote only after comparing branches/commits and confirming no unrelated history will be pushed.
3. After the source/remote relationship is correct, Tom must make the intended repository public (or intentionally change every “public” statement to “private interview artifact”). The portfolio recommendation is public visibility because the locked purpose is stranger-readable GitHub evidence.
4. Verify the public repository with an unauthenticated browser session, then confirm its README, default branch, license, Actions status, and assets are the expected AlphaGuard ones.

**Tradeoff:** Public visibility exposes the intentionally public lab code and documentation, but not secrets if the documented `.env` discipline has been followed. Keeping it private avoids that exposure but forfeits the primary cold-reader portfolio use case.

#### P0-2 — README’s Option B metric example contradicts the finance-honesty and training-data source

**Evidence**

- `README.md` lines 106–107 says the local manifest has train F1 approximately 0.73 and **test F1 = 0.0** with two positives.
- `docs/FINANCE_HONESTY.md` lines 21–30 says the post-alias local manifest has train F1 approximately 0.693, **test F1 approximately 0.087**, and **three** test positives; it explicitly identifies the 0.0/two-positive result as the *prior pre-alias* manifest.
- `docs/TRAINING_DATA.md` line 148 repeats the 0.087/three-positive current example.

**Why this is a portfolio blocker**

This is a direct numerical contradiction on the page a recruiter will read first. The weaker metric itself is not the credibility problem; an unexplained disagreement about which result is current is. It makes a reviewer question data lineage, reproducibility, and whether the result was selectively reported.

**Smallest remediation**

Choose one dated local-manifest example as the canonical cited result. The evidence supports using the 2026-07-21 post-alias result (`train F1 ≈0.693`, `test F1 ≈0.087`, test positives = 3, with its confusion matrix) and labeling it as a non-committed, locally regenerated artifact. Update the README’s limitation bullet and ensure `FINANCE_HONESTY.md` and `TRAINING_DATA.md` retain identical values, date, and provenance. Do not place the stale 0.0 figure in the README unless it is explicitly described as superseded historical evidence.

**Tradeoff:** Showing weak holdout numbers can reduce superficial appeal, but it demonstrates the metric discipline senior interviewers expect and avoids an avoidable integrity failure.

### P1 — Fix in the same documentation-alignment delivery

#### P1-1 — VISION retains legacy observability and public-sharing requirements that conflict with current packaging truth

**Evidence**

- `docs/VISION.md` line 81 says v1 is done with a “LangSmith trace,” lines 53 and 267 call for LangSmith/Phoenix trace screenshots, and line 311 says screenshots are required.
- The same document’s current status line (line 5), README (lines 74–84), `GETTING_STARTED.md` line 55, and `docs/assets/README.md` lines 10–15 correctly say the mandatory baseline is a local run summary and that LangSmith/Phoenix are conditional/fail-open; default screenshots show both as skipped.
- `VISION.md` line 301 says the repository is public, while the authenticated GitHub repository lookup says it is private.

**Impact**

The product SSOT tells two different stories: bounded local evidence is enough today, but a reader can also infer a required external trace screenshot and already-public repository. That creates unnecessary interview questions and pressures future updates toward fabricated or overstated observability evidence.

**Smallest remediation**

In the Align-docs pass, replace legacy “LangSmith (or Phoenix) trace screenshots required” language with “local run summary evidence required; real LangSmith/Phoenix evidence only when a configured run is actually captured.” Change visibility language only after Tom’s P0-1 decision: confirm public after the verified release, or call it a planned distribution state without claiming it is current.

#### P1-2 — The first-minute README lacks a direct link to the finance-honesty evidence and readable proof hierarchy

**Evidence**

- The opening status paragraph (`README.md` lines 3–7) correctly distinguishes fixture plumbing from Option B, but a reader reaches the current Option B numbers only deep in Limitations (lines 98–111).
- The Finance Honesty document has the relevant scope statement, current metric table, split counts, and explicit “not alpha / no PnL” boundary (`docs/FINANCE_HONESTY.md` lines 1–30).

**Impact**

A cold reviewer can skim “XGBoost downside-risk gate” and “local + CI” without encountering a compact statement of what is proven, what is merely a local lab result, and where its current metric source lives.

**Smallest remediation**

Add one short README “Evidence and limits” callout immediately after the opening paragraph or architecture diagram: fixture replay proves integration; Option B is a local lab model with weak/noisy holdout metrics; the gate is not alpha, PnL, or a production risk model; link to `FINANCE_HONESTY.md`. Keep the detailed table in the finance document rather than duplicating full metrics throughout the README.

**Tradeoff:** A slightly denser first screen costs a few lines but sharply reduces the risk of a misleading skim.

#### P1-3 — The screenshot set is structurally honest but not current-release evidence

**Evidence**

- The assets documentation identifies their sole source run as 2026-07-13 (`docs/assets/README.md` line 17).
- The package later added Option B training, RSS polling, and conditional LangSmith/Phoenix adapters; the screenshots are still truthful for the default fixture smoke but do not prove that current-release packaging was run.

**Impact**

Age alone does not prove a screenshot is invalid, so this is not a claim that the assets are false. It does mean they should not be presented as fresh evidence for later functionality.

**Smallest remediation**

After P0-1 resolves the authoritative checkout and dependencies are installed, run the current default smoke, redact paths, and refresh the asset provenance date. Keep the image captions explicit that they prove fixture replay/local-envelope behavior only. Do not add fake cloud-observability images; optional live-provider evidence should be captured only from an actual configured run.

### P2 — Valuable polish; do not delay the P0/P1 fixes

#### P2-1 — The README can reduce first-minute cognitive load

The status paragraph is careful but long and uses implementation labels (`05a`, `05b`, `bundle_kind`) before a reader sees the system diagram. A short “What you can verify in five minutes” row—clone smoke, inspect local envelope, run tests/CI, then read finance limits—would improve sequencing without changing claims.

#### P2-2 — `INTERVIEW.md` is strong as a defense document but should remain secondary navigation

Its 17 themes give Tom concrete answers about leakage, deterministic policy, and observability. It is deliberately technical and correctly labels itself as a staff-interview FAQ. Avoid moving that depth into the README; link to the most relevant sections from a compact README proof hierarchy instead.

#### P2-3 — Make CI evidence easier to inspect after P0-1

The workflow is minimal and appropriate: Python 3.12, frozen dependency synchronization, and default pytest. Once the correct repository is public, add a truthful CI status badge or a pinned successful run link only if it points to the actual AlphaGuard Actions workflow. Do not imply smoke/Ollama/Kafka tests run in CI; the current workflow does not run them.

## What is actually strong

- The README, getting-started path, FAQ, finance-honesty document, and asset captions repeatedly preserve the most important boundary: this is a replay-first, local interview lab—not a deployed trading system or return-prediction claim.
- Fixture-versus-Option-B separation is explicit in every major document. This is an unusually good defense against synthetic-fixture metric theater.
- The technical interview material explains real engineering controls: as-of filtering, application-owned identity, deterministic gating, fail-closed schema handling, and the distinction between default smoke and optional services.
- License language is consistently clear: PolyForm Noncommercial is source-available and non-commercial, not MIT or OSI open source.

## Decision flags for Tom

### Decision: Repair and publish the actual AlphaGuard repository

**In plain terms:** The current local folder is connected to the Polk County repository, while the intended AlphaGuard repository exists but is private. A public README cannot help as a portfolio artifact until the source checkout, remote, and GitHub visibility all refer to the same project.

**Options**

1. Reclone/verify `Alpha-W0lf/alphaguard`, make it public, then perform documentation alignment there.
2. Repair this checkout’s remote after a branch/commit comparison confirms it is truly the AlphaGuard working tree.
3. Keep AlphaGuard private and change its documentation so it no longer claims public GitHub sharing.

**Recommendation:** Option 1 unless Tom has already independently verified this folder is the intended AlphaGuard Git history. It provides the safest rollback path and avoids accidentally pushing unrelated Polk County history.

**Tradeoffs:** Re-cloning costs a small amount of setup time; in-place remote repair is faster but has the highest contamination risk. Remaining private avoids public exposure but defeats the stated cold-reader portfolio purpose.

**Needs from Tom:** Authorize either “reclone and publish AlphaGuard” or “verify and repair this checkout’s remote”; explicitly choose private-only only if portfolio distribution is being parked.

### Decision: Use the post-alias Option B metric as the only current public example

**In plain terms:** Three documents agree that the newer local example is test F1 approximately 0.087 with three positives; the README still displays an older zero-F1/two-positive run.

**Options**

1. Use the 2026-07-21 post-alias result everywhere and archive the older result as historical context only.
2. Omit numerical metrics from the README but retain them in the finance-honesty page.
3. Keep both results in the README with full provenance.

**Recommendation:** Option 1, plus a short README link to the finance-honesty source. It is the clearest current claim with enough context for skeptical readers.

**Tradeoffs:** One concise current figure is easy to audit; omitting it reduces visible rigor; showing both adds detail but makes first-minute reading worse.

**Needs from Tom:** Authorize the post-alias metric wording for the Align-docs pass.

## Smallest ordered remediation set for an Align-docs follow-on

1. **P0 delivery safety (Tom + ops, before docs):** resolve the authoritative AlphaGuard checkout/remote and repository visibility. Do not push from the current checkout until that is verified.
2. **P0 documentation integrity:** update the README’s Option B numbers and provenance to the post-alias finance-honesty source; grep the public-facing documents for old 0.0/two-positive language.
3. **P1 status alignment:** revise VISION legacy public/required-trace screenshot language so it matches the local-envelope, conditional-observability reality and the final visibility decision.
4. **P1 cold-reader clarity:** add the compact README evidence-and-limits callout linking to Finance Honesty; retain full metrics in one canonical document.
5. **P1 evidence refresh:** after the authoritative repository can run the stated commands, generate fresh default-smoke assets and record their date/scope.
6. **P2 discoverability:** only then add a truthful CI badge/link and a compact five-minute verification sequence.

No Guide 09 feature, model-policy revision, live-trading functionality, agent-on-consume work, or LEMON/tax work is justified by this review.

## Critical review Definition of Done and next stage

| Check | Result |
|---|---|
| Verdict and ranked P0/P1/P2 findings with evidence | **Met** |
| Decision flags and tradeoffs | **Met** |
| Smallest remediation set | **Met** |
| Findings persisted | **Met** — this document |
| No silent implementation/refactor | **Met** |
| Ready for Align docs | **Conditionally yes** — after Tom selects the P0 remote/visibility path and canonical metric wording |
| Ready for cold public portfolio use | **No** — P0-1 and P0-2 remain open |

## Learning notes — interview-portable

- **Claim-to-evidence traceability:** Every portfolio claim should point to a reproducible artifact. Here, a model metric needs its manifest date, sample split, and document owner; otherwise a reviewer cannot tell whether it is current.
- **Data lineage:** Lineage means being able to explain where a number came from and what transformed it. The pre-alias versus post-alias metric discrepancy is exactly the kind of lineage question ML interviewers use to test rigor.
- **Reproducible builds:** A clone URL, Git remote, lockfile/dependency setup, and CI workflow must describe the same project. A correct README cannot compensate for a checkout whose remote points at unrelated history.
- **Fail-open observability:** A fail-open trace adapter records telemetry when configured but does not block the core application if the provider is unavailable. It is valid for a lab, but portfolio docs must say what the default run actually emits.
