---
name: ll-patch-capture
description: ADR-049 governed skill for dual-path experience patch registration (Prompt-to-Patch + Document-to-SRC routing).
---

# LL Patch Capture

This skill implements the ADR-049 dual-path experience patch registration. It accepts either free-form user prompts describing a UX change or structured documents from upstream product workflows, classifies the input, and routes it to generate a properly structured experience patch.

## Canonical Authority

- ADR: `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md`
- Upstream handoff: user prompt or `ll-product-raw-to-src` output
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

1. **Accept input** — either free-form prompt text (user describes UX change) or document path (BMAD/Superpowers/OMC output).
2. **Route detection** — classify input as `"prompt"` (free-form text) or `"document"` (file path to structured document).
3a. **Prompt-to-Patch path**: Executor Agent analyzes change description, generates Patch YAML draft with all fields pre-filled per ADR-049 decision tree, writes to `ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml`.
3b. **Document-to-SRC path**: Route to `ll-product-raw-to-src` skill; if experience-layer change detected, generate semantic Patch with `resolution.src_created = SRC ID`.
4. **Supervisor Agent** validates generated Patch — runs schema validation via `cli/lib/patch_schema.py`, checks for conflicts, decides auto-pass vs escalate to human.
5. **Auto-pass** → register Patch, update `patch_registry.json`, emit "已登记 UXPATCH-XXXX" notification.
6. **Escalate** → present structured review checklist to user for confirmation.
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
