---
name: ll-experience-patch-settle
description: ADR-049 governed skill for settling validated Minor Experience Patches with backwrite RECORDS for human review.
---

# LL Experience Patch Settle

This skill implements the ADR-049 Minor patch settlement workflow. It accepts validated Patch YAML files (grade_level=minor) from the upstream `ll-patch-capture` skill, creates structured backwrite RECORDS in a `backwrites/` subdirectory for human review, and updates the Patch status to "applied".

**Critical clarification:** Backwrite creates RECORDS (structured YAML summaries) -- NOT actual SSOT file modifications. A future `--apply` flag would perform actual SSOT modification, gated behind human confirmation. For current scope, only the record-writing path is implemented.

Major patches (grade_level=major) are REJECTED immediately with a message directing users to `ll-frz-manage --type revise`.

## Canonical Authority

- ADR: `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` §4.4 (settlement rules)
- ADR: `ssot/adr/ADR-050-SSOT语义治理总纲.md` §6.2 (Minor settle behavior)
- Upstream handoff: `ll-patch-capture` (validated Patch YAML with grade_level=minor, status=approved)
- Downstream consumer: backwrite records in `ssot/experience-patches/{feat_ref}/backwrites/` subdirectory

## Runtime Boundary Baseline

- Interpret this workflow using `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Minor Experience Patch Settlement`.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `scripts/settle_runtime.py`

## Execution Protocol

1. **Accept Patch YAML input** -- validated by upstream, must have `status: approved` and `grade_level: minor`.
2. **Verify grade_level** -- if "major", reject immediately with message: "Major patches must use ll-frz-manage --type revise".
3. **Idempotency check** -- if `status` is already "applied", return early (no-op, not an error).
4. **Determine backwrite targets** -- look up `change_class` in BACKWRITE_MAP to get the list of backwrite targets.
5. **Write backwrite RECORDS** -- for each target, write a structured YAML record to `ssot/experience-patches/{feat_ref}/backwrites/{target}_updates.yaml`. These are RECORDS for human review, NOT actual SSOT file modifications.
6. **Update Patch status** -- set `status: applied` and `settled_at: <ISO timestamp>`.
7. **Validate output** -- confirm Patch YAML was updated correctly.

## BACKWRITE_MAP

| change_class | must_backwrite_ssot | backwrite_targets |
|---|---|---|
| ui_flow | False | ui_spec_optional |
| copy_text | False | (none) |
| layout | False | ui_spec_optional |
| navigation | True | ui_spec, flow_spec |
| interaction | True | ui_spec, flow_spec, testset |
| error_handling | False | (none) |
| performance | False | (none) |
| accessibility | False | ui_spec_optional |
| data_display | False | ui_spec_optional |
| visual | False | ui_spec_optional |
| semantic | True | frz_revise (NOT handled by settle) |
| other | False | (none) |

## Workflow Boundary

- Input: validated Patch YAML (grade_level=minor, status=approved) from `ll-patch-capture`
- Output: updated Patch YAML (status=applied) + backwrite RECORDS in `backwrites/` subdirectory
- Out of scope: actual SSOT file modification (future `--apply` flag), Major patch processing (routed to FRZ revise)

## Non-Negotiable Rules

- **Do NOT process Major patches** -- reject immediately and route to `ll-frz-manage --type revise`.
- **Do NOT modify actual SSOT files** -- backwrite creates RECORDS only. A future `--apply` flag would perform actual SSOT modification, gated behind human confirmation.
- **Settle is idempotent** -- running settle on an already-applied patch is a no-op (not an error).
- **Do NOT skip test_impact review** -- TESTSET backwrite record required when `test_impact.affected_routes` is non-empty.
- **Use `yaml.safe_load()` only** -- no `yaml.load()` for YAML deserialization.
- **Import `derive_grade` from `cli/lib/patch_schema.py`** -- do NOT re-implement grade derivation locally.
- **All consumers switching on ChangeClass must have an explicit `other` fallback** to handle unknown values gracefully.
