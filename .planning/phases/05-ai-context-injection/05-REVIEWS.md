---
phase: "05"
reviewers: [gemini, codex, opencode]
reviewed_at: "2026-04-17T15:37:00Z"
plans_reviewed: ["05-01-PLAN.md", "05-02-PLAN.md"]
---

# Cross-AI Plan Review — Phase 05

## Gemini Review

**Status:** Failed — Gemini CLI returned empty output or timed out.

## Codex Review

### Plan 05-01: Python patch-aware context resolver + CLI wrapper

**Summary:** The plan correctly reuses Phase 4's `resolve_patch_context(feat_ref)` as core dependency and adds an awareness recording script, aligning with D-01/D-07/D-09. However, there is a mismatch between the phase success criteria (which mention `patch-context.yaml`) and the plan's output (`patch-awareness.yaml`). The injection chain and patch filtering rules (D-08) need clarification.

**Strengths:**
- Reuses Phase 4, reducing duplication risk (D-07)
- Correctly positions Phase 5 as awareness recording, not enforcement (D-01/D-03)
- Clear function layering (summarize/write/resolve/main) supports testing and reuse
- Introduces context budget concept for AI context capacity

**Concerns:**
- **[HIGH] Requirement/output mismatch:** REQ-PATCH-05 and success criteria specify `patch-context.yaml` (AI-readable), but the plan produces `patch-awareness.yaml` without a clear step to generate the former
- **[HIGH] Missing injection chain:** The plan only "generates records" but doesn't clarify how patch context gets injected "before AI generates code" (success criteria 3/4)
- **[HIGH] D-08 filtering may conflict:** Roadmap/REQ says "active/resolved" but D-08 says "only validated + pending_backwrite"; plan doesn't document the filtering logic
- **[MEDIUM] run.sh cross-platform risk:** Project runs on Windows/PowerShell; `run.sh` may not be available
- **[MEDIUM] Context trimming too crude:** Simple ">5 patches" protection may lose critical patches; needs explainable sorting/grouping strategy
- **[MEDIUM] Security/prompt injection risk:** Patch content is controlled input; if directly concatenated into AI context, it could be treated as instructions
- **[LOW] Import coupling unclear:** Phase 4 import path stability, workspace root detection within skill, and relative import strategy need clarification

**Suggestions:**
- Have the script output **both** `patch-context.yaml` (for AI reading) and `patch-awareness.yaml` (for audit trail)
- Clarify patch filtering to align with D-08: only include validated + pending_backwrite, log excluded count for transparency
- Replace crude ">5 truncate" with priority-based sorting (status priority, most recent, impact scope, risk level); degrade tail patches to metadata-only with pointer
- Strengthen "data isolation" format in `patch-context.yaml`: treat patch content as field data, avoid imperative natural language, quote free-text fields explicitly
- Make wrapper more universal: prefer `python -m ...` or `run.ps1` as alternative, ensure workspace-root detection doesn't depend on *nix toolchain
- Add minimal test suggestions: pytest cases for D-08 filtering, sorting/trimming, empty directory, bad YAML, duplicate patch_id, missing path

**Risk Assessment: MEDIUM-HIGH** — Core capability is implementable but the plan doesn't fully close the loop on `patch-context.yaml` + injection chain alignment with REQ-PATCH-05 and success criteria.

---

### Plan 05-02: Skill definition (SKILL.md, contracts, executor)

**Summary:** Wrapping Phase 5's "injection action" as a new skill (`ll-patch-aware-context`) with full contracts/lifecycle/executor is engineering-sound. However, the executor's "evaluate patches → proceed" flow risks sliding into enforcement (violating D-03), and the plan doesn't cover "the lightest injection point into existing SSOT chain skills" (success criteria 3/4), which may result in "skill exists but main chain doesn't call it."

**Strengths:**
- Skill delivery matches existing SSOT chain organization, supporting reuse and tracking
- Contracted interfaces (input/output) stabilize interfaces, reducing SSOT drift
- "Record consideration" mechanism aligns with D-09 (awareness form recorded)
- If executor is well-written, can be "usable without changing original skills" (D-02/D-10 friendly)

**Concerns:**
- **[HIGH] Main chain integration gap:** Success criteria require "automatic injection before AI generates code" and mention integrating injection steps into skill's `executor.md`; this plan only creates the new skill's executor without specifying how to trigger injection before actual code-generation skills execute (D-02 says original skills are unaffected, requiring a clear "optional injection" mechanism)
- **[HIGH] May slide into enforcement:** If executor's "evaluate patches" includes "must follow/reject generation" semantics, it violates D-03; must strictly limit to "read and record known optimizations/risk reminders," not enforcement
- **[MEDIUM] Product naming/contract alignment unclear:** Contracts "matching awareness recording schema," but Phase 5's key product is `patch-context.yaml` (AI-readable) + awareness record (D-09); aligning only with awareness schema may be insufficient
- **[MEDIUM] D-08 injection scope needs contract lock:** If contracts allow injecting all active/resolved, it conflicts with D-08; should explicitly output only validated + pending_backwrite in schema/contract, record excluded items without injection
- **[LOW] D-10 "lightest injection" constraint:** 5-step protocol, if written too long or requiring complex interaction, may indirectly push rewrites of other skill executors; needs to be designed as "a single-line referenceable prerequisite step"

**Suggestions:**
- In SKILL.md / executor.md, clarify: this skill **only does two things**: 1) generate/update `patch-context.yaml` (AI reading), 2) generate/update `patch-awareness.yaml` (audit record, D-09), and **does not block subsequent generation** (D-01/D-03)
- Design "lightest integration point" (align with success criteria 3/4 + D-02/D-10):
  - Option A (recommended): Add an **optional prerequisite** in executors that need codegen: "If patch registry exists, first run `ll-patch-aware-context` to generate `patch-context.yaml`, then begin code generation"; doesn't change original skill structure, only adds prerequisite read/generation step
  - Option B: Orchestrator/runner auto-calls this skill before invoking codegen skill (but must ensure D-04 "user trigger" boundary is respected)
- Make D-08 a hard constraint in contracts: output only contains `injected_patches` (validated/pending_backwrite), add `excluded_patches` for metadata and exclusion reasons only
- Use "awareness tone" in executor copy: "consider / acknowledge / record", avoid "must / enforce / reject / block"
- Add traceability fields to output contract: `patch_ids`, source file paths, hash, generation time, resolver version

**Risk Assessment: MEDIUM** — Skill engineering is solid, but without filling "main chain injection trigger point" and "`patch-context.yaml` as AI input" contract, there's risk of "skill complete but nobody calls it / calling only produces awareness."

---

## OpenCode Review

**Status:** Failed — OpenCode returned empty output (1 line).

---

## Consensus Summary

**Reviewed by:** 1 AI system (Codex). Gemini and OpenCode failed to return results.

### Key Concerns from Codex Review

1. **Output naming mismatch** [HIGH] — Plans produce `patch-awareness.yaml` but REQ-PATCH-05 and ROADMAP success criteria mention `patch-context.yaml` as the AI-readable format. Need to either rename the output or produce both files.

2. **Main chain integration gap** [HIGH] — Plans create a new skill but don't specify how existing SSOT chain skills will invoke it as a prerequisite without modifying their executor.md files (D-02, D-10). The "lightest injection" mechanism needs explicit design.

3. **D-08 filtering needs contract lock** [MEDIUM] — Plans should explicitly document that only `validated` + `pending_backwrite` patches are injected, with excluded patches logged separately.

4. **Context budget strategy too crude** [MEDIUM] — The ">5 patches" trimming needs priority-based sorting rather than simple truncation.

5. **Cross-platform wrapper risk** [MEDIUM] — `run.sh` may not work on Windows; consider `run.ps1` or `python -m` alternative.

### Divergent Views

No divergence to report — only one reviewer provided substantive feedback.

---

*Review completed: 2026-04-17*
*1 of 3 attempted reviewers succeeded (Codex)*
