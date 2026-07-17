# Align-docs — AlphaGuard Guide 07 LangSmith fail-open spans (pass 127)

**Date:** 2026-07-17  
**Mode:** spoke  
**Stage:** Align docs  
**Guide:** `docs/dev_guides/2026-07-17_dev_guide_07_langsmith_fail_open_spans.md`  
**Review:** `docs/2026-07-17_guide07_langsmith_fail_open_review.md` (shippable as-is)  
**Implement:** `287a82a`  
**Handoff:** `second_brain/docs/2026-07-17_spoke_alphaguard_guide07_align_pass127_handoff.md`

## What was aligned

| Doc | Change |
|-----|--------|
| Inventory context | Superseded Gather “LS/Phoenix status stubs” prose; Guide 07 outcome table; post-07 candidate status; Align Met |
| VISION | Last Updated → Align Met; Status already had Guide 07; **MV walkthrough/daily-prep still unchecked** |
| ARCHITECTURE | Stack + §6 step 9 + §7.8 adapters + critical path: LangSmith real when configured; Phoenix stub |
| Guide 07 | Status **Aligned / slice closed** |
| Review note | Soft Gather-prose finding → Closed Align pass 127 |

## Explicitly untouched (by lock)

- VISION MV walkthrough / daily-prep checkboxes — remain `[ ]`
- Phoenix real spans — not claimed
- D3 live LangSmith probe — residual parked
- No Guide 08 invent

## Remaining residuals (parked)

- Optional D3 live operator probe  
- Optional update_run-failure unit test  
- Phoenix real spans / agent-on-consume / live-Ollama eval rates → need new hub Prioritize  

## Align DoD

- [x] Stale/conflicting Guide 07 status fixed  
- [x] Status/checkboxes match reality (MV human boxes still open)  
- [x] No “docs later” leftover for Guide 07 facts  
- [x] No Guide 08 without new handoff  

## Stop

Align Met. **Slice closed.** Await hub Prioritize for any next work item.
