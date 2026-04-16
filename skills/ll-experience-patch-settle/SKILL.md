---
name: ll-experience-patch-settle
description: ADR-049 governed skill for batch patch settlement — reads pending_backwrite patches, classifies by change_class, generates delta drafts and SRC candidates, updates statuses, and produces settlement report.
---

# LL Experience Patch Settle

This skill implements the ADR-049 experience patch settlement workflow. It reads `pending_backwrite` patches from a FEAT directory, groups them by `change_class`, generates appropriate delta drafts or SRC candidates, updates patch statuses atomically, and produces a settlement report.

## Canonical Authority

- ADR: `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` (Sections 4.4, 7, 8, 12.3)
- Upstream handoff: `ll-patch-capture` (produces pending_backwrite patches)
- Downstream consumer: Phase 4 — TESTSET linkage

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. **Accept feat_id + workspace input** — identify the FEAT directory at `ssot/experience-patches/{feat_id}/`.

2. **Scan** `ssot/experience-patches/{feat_id}/` for `pending_backwrite` patches (UXPATCH-*.yaml files).

3. **Group patches by change_class** (D-09): visual, interaction, semantic.

4. **For each group, process per backwrite mapping** (D-02, D-03, D-04):
   - **visual → retain_in_code** (D-02): no SSOT backwrite, mark status as resolved
   - **interaction → delta generation** (D-03): generate ui-spec-delta.yaml + flow-spec-delta.yaml + test-impact-draft.yaml
   - **semantic → SRC candidate** (D-04): generate SRC-XXXX__{slug}.yaml candidate requiring gate approval

5. **Generate delta/SRC content** via executor agent — AI fills in structured YAML drafts based on patch content.

6. **Update patch statuses + patch_registry.json** — atomic batch status update to terminal states.

7. **Produce resolved_patches.yaml** settlement report recording each patch's resolution method, timestamp, and operation summary.

## Backwrite Mapping (per ADR-049 Section 4.4)

| change_class | Action | Terminal Status | Output |
|-------------|--------|----------------|--------|
| visual | retain_in_code (D-02) | retain_in_code | No delta files |
| interaction | generate deltas (D-03) | backwritten | ui-spec-delta.yaml, flow-spec-delta.yaml, test-impact-draft.yaml |
| semantic | SRC candidate (D-04) | upgraded_to_src | SRC-XXXX__{slug}.yaml |

## Escalation Conditions (D-10)

- **change_class ambiguity**: patch cannot be clearly classified — flag for human review
- **test_impact uncertainty**: test_impact fields insufficient for impact analysis — flag for human review
- **same-file multi-patch conflicts**: multiple patches modify the same file differently — escalate to human

## Workflow Boundary

- **Input**: feat_id + workspace
- **Output**: resolved_patches.yaml + delta files + updated patch_registry.json
- **Out of scope**: TESTSET linkage (Phase 4), Hook integration (Phase 6), 24h blocking (Phase 7), actual SSOT merge (future milestone per D-05)

## Non-Negotiable Rules

- Do not modify any frozen SSOT files (D-05)
- Do not skip schema validation before processing each patch
- Delta files MUST include original_text, proposed_change, rationale fields (D-06)
- Default to automated processing (D-08); escalate only on D-10 conditions
