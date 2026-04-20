---
name: ll-patch-capture
description: ADR-049 governed skill for dual-path experience patch registration (Prompt-to-Patch + Document-to-SRC routing) with tri-classification grading.
---

# LL Patch Capture

This skill implements the ADR-049 dual-path experience patch registration. It accepts either free-form user prompts describing a UX change or structured documents from upstream product workflows, classifies the input via tri-classification (visual/interaction/semantic), derives Minor/Major grade level, and routes it to generate a properly structured experience patch.

## Canonical Authority

- ADR: `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md`
- ADR: `ssot/adr/ADR-050-SSOT语义治理总纲.md` §6 (change grading)
- Upstream handoff: user prompt or `ll-product-raw-to-src` output
- Downstream consumer: `ll-experience-patch-settle` (Minor settle) / `ll-frz-manage --type revise` (Major)

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

1. **Accept input** — either free-form prompt text (user describes UX change) or document path (BMAD/Superpowers/OMC output).
2. **Route detection** — classify input as `"prompt"` (free-form text) or `"document"` (file path to structured document).
2b. **Tri-classification**: Classify input as visual, interaction, or semantic. Scan ALL indicator lists using `skills/ll-patch-capture/scripts/patch_capture_runtime.py` `classify_change()`. If semantic indicator matches -> GradeLevel.MAJOR (semantic dominates). If multiple same-grade dimensions (e.g., visual + interaction) -> confidence=medium. If no indicators match -> fallback to file-pattern classification via `_fallback_classify_by_paths()` (replicates `_suggest_change_class` from `cli/lib/patch_auto_register.py`). Set needs_human_review=True for low-confidence cases.
3a. **Prompt-to-Patch path**: Executor Agent analyzes change description, generates Patch YAML draft with all fields pre-filled per ADR-049 decision tree. Set `grade_level`, `dimensions_detected`, `confidence`, and `needs_human_review` fields based on classification result. Use `cli/lib/patch_schema.py` `derive_grade()` for deterministic mapping. Writes to `ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml`.
3b. **Document-to-SRC path**: Route to `ll-product-raw-to-src` skill; if experience-layer change detected, generate semantic Patch with `resolution.src_created = SRC ID`.
4. **Supervisor Agent** validates generated Patch — runs schema validation via `cli/lib/patch_schema.py`, checks for conflicts, decides auto-pass vs escalate to human.
5. **Auto-pass** (sub-process of capture) -> Supervisor approves without human review when confidence is high and no conflicts detected. Register Patch, update `patch_registry.json`, emit "已登记 UXPATCH-XXXX" notification.
6. **Escalate** (sub-process of capture) -> Supervisor flags ambiguity or conflicts, presents structured review checklist to user for confirmation. After human confirmation, register Patch same as auto-pass.
7. **Validate output** — confirm generated YAML passes schema validation, registry updated.

## Workflow Boundary

- Input: user prompt text describing UX change OR document path to raw product requirements
- Output: Patch YAML file in `ssot/experience-patches/{FEAT-ID}/` + updated `patch_registry.json`
- Out of scope: settlement (Phase 3), test linkage (Phase 4), hook auto-trigger (Phase 6), AI context injection (Phase 5), 24h blocking (Phase 7)

## Non-Negotiable Rules

- Do not generate a Patch YAML without running schema validation (`cli/lib/patch_schema.py` `validate_file`).
- Do not auto-submit Patch without Supervisor validation pass.
- Do not write `source.human_confirmed_class` as null — must match `source.ai_suggested_class` in auto-pass mode.
- Do not bypass dual-path routing — always classify input as prompt or document first.
- Document-to-SRC path delegates to `ll-product-raw-to-src`; this skill only routes and associates.
- All AI pre-filled fields must be marked as human-reviewed per ADR-049.
- Patch IDs must be sequential `UXPATCH-NNNN` format derived from `patch_registry.json` max sequence number.
- **Do not generate Patch without grade_level field** — derive from change_class via `derive_grade()`. If needs_human_review=True, flag for human confirmation before proceeding.
- All consumers switching on ChangeClass must have an explicit `other` fallback to handle unknown values gracefully (backward-compat requirement).

## Tri-Classification Reference

| Top-Level Class | Sub-Classes | Grade Level | Routing |
|----------------|-------------|-------------|---------|
| visual | ui_flow, copy_text, layout, navigation, data_display, accessibility | Minor | ll-experience-patch-settle |
| interaction | interaction | Minor | ll-experience-patch-settle (backwrite to UI Spec, Flow Spec, TESTSET) |
| semantic | semantic | Major | ll-frz-manage --type revise (FRZ re-freeze) |
| other | — | Minor (human can escalate) | ll-experience-patch-settle |

**Confidence levels:**
- `high`: Single dimension matched with no ambiguity
- `medium`: Multiple same-grade dimensions matched, or semantic dominates mixed input
- `low`: Fallback to file-pattern classification or no indicators matched -> needs_human_review=True
