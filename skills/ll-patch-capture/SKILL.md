---
name: ll-patch-capture
description: ADR-049 governed skill for dual-path experience patch registration (Prompt-to-Patch + Document-to-SRC routing).
---

# LL Patch Capture

This skill implements the ADR-049 dual-path experience patch registration workflow. It accepts either free-form user prompts describing UX changes or structured document paths, classifies the input, routes it through the appropriate path, and produces a validated Patch YAML file registered in the patch registry.

## Canonical Authority

- ADR: `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md`
- Upstream handoff: user prompt (free-form) or `ll-product-raw-to-src` output (document path)
- Downstream consumer: `ll-experience-patch-settle` (Phase 3)

## Runtime Boundary Baseline

- Interpret this workflow using `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Experience Change -> Patch Registration`.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. **Accept input** — receive either free-form prompt text (user describes UX change) or document path (BMAD/Superpowers/OMC output file path).

2. **Route detection** — classify input as one of two paths:
   - `"prompt"`: free-form text describing a UX change
   - `"document"`: absolute file path to a structured requirements document

3. **Execute the appropriate path:**

   **Step 3a — Prompt-to-Patch path (small changes):**
   - Executor Agent analyzes the change description against the ADR-049 decision tree (Section 2.4: three independent gates)
   - Classifies the change as `visual`, `interaction`, or `semantic`
   - Generates a Patch YAML draft with all fields pre-filled per ADR-049 Section 5.3 schema
   - Marks AI-prefilled fields (`change_class`, `test_impact`, `backwrite_targets`) as `human-reviewed`
   - Writes draft to `ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml`

   **Step 3b — Document-to-SRC path (large changes):**
   - Route to `ll-product-raw-to-src` skill for structured document processing
   - If experience-layer change is detected during SRC generation, generate a semantic Patch as an associated record
   - Set `resolution.src_created` = SRC ID to link the Patch to the new SRC

4. **Supervisor Agent validates generated Patch:**
   - Runs schema validation via `cli/lib/patch_schema.py validate_file` against the generated Patch YAML
   - Checks for conflicts with existing active/validated Patches under the same FEAT (scan `changed_files` overlap)
   - Decides auto-pass (schema valid, no conflicts) vs escalate to human (schema errors, conflicts, or semantic classification requires review)

5. **Auto-pass path** — register the Patch:
   - Update `patch_registry.json` with new entry (id, status, change_class, created_at, title, patch_file)
   - Emit "已登记 UXPATCH-XXXX" notification
   - Patch enters `draft` status, transitions to `active` once agent begins code changes

6. **Escalate path** — present structured review to user:
   - Display classification rationale with decision tree evaluation
   - Show schema validation errors or conflict details
   - Present checklist of fields requiring human confirmation
   - Wait for user confirmation or modification before proceeding

7. **Validate output** — confirm the generated YAML passes all checks:
   - Schema validation via `cli/lib/patch_schema.py validate_file`
   - Registry updated with new entry
   - Patch file written to correct directory with sequential ID

## Workflow Boundary

- **Input**: user prompt text describing UX change OR document path to raw product requirements
- **Output**: Patch YAML file at `ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml` + updated `patch_registry.json`
- **Out of scope**: settlement (Phase 3), test linkage (Phase 4), hook auto-trigger (Phase 6), AI context injection (Phase 5), 24h blocking (Phase 7)

## Non-Negotiable Rules

- Do not generate a Patch YAML without running schema validation (`cli/lib/patch_schema.py validate_file`)
- Do not auto-submit Patch without Supervisor validation pass
- Do not write `source.human_confirmed_class` as null — must match `source.ai_suggested_class` in auto-pass mode
- Do not bypass dual-path routing — always classify input as prompt or document first
- Document-to-SRC path delegates to `ll-product-raw-to-src`; this skill only routes and associates
- All AI pre-filled fields must be marked as human-reviewed per ADR-049 Section 12.2
- Patch IDs must be sequential UXPATCH-NNNN format derived from `patch_registry.json` max sequence
