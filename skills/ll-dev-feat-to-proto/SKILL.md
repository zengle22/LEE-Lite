---
name: ll-dev-feat-to-proto
description: Governed workflow skill for transforming one frozen FEAT into a static HTML interactive prototype package with complete journey flow, UX button responses, and structured human review gating before UI spec derivation.
---

# LL Dev FEAT to Proto

This skill converts one selected frozen FEAT into one governed `prototype_package`.
The output is a static HTML prototype, not production frontend code.

## Journey Hi-Fi Dedup

When the selected FEAT belongs to a known journey (e.g. `SRC001`, `SRC002`) that requires a hi-fi template, the workflow emits a **single journey-level prototype package** (e.g. `SRC001-JOURNEY`) and reuses the same `artifacts_dir` across FEATs in that journey to avoid 001-005 producing duplicate prototypes.

## Runtime Boundary

- Interpret this skill through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-041-FEAT-to-PROTOTYPE 前增加 Journey ASCII 产物并引入固定 UI Shell 引用基线.MD`.
- This skill stops at experience prototyping and review gating.
- It does not emit final `ui_spec_package`.

## Run Protocol

1. Read `ll.contract.yaml`, `input/contract.yaml`, and `output/contract.yaml`.
2. Accept only one governed `feat_freeze_package` plus an explicit `feat_ref`.
3. `--input` may be either the FEAT package directory or a `formal.feat.*` admission ref.
4. Run `python scripts/feat_to_proto.py run --input <feat-package-dir-or-formal-ref> --feat-ref <feat-ref> --repo-root <repo-root>`.
5. Generate:
   - `journey-ux-ascii.md` as the Journey Structural Spec
   - `ui-shell-spec.md` as a snapshot of the fixed UI Shell Source
   - `prototype/journey-model.json` as the journey-level surface + main-path map used by downstream gates and reviewers
   - a static HTML prototype
6. Resolve the frozen `surface_map_package` first and carry its `surface_map_ref`, `prototype_owner_ref`, `prototype_action`, `ui_owner_ref`, and `ui_action` into the emitted bundle.
7. The shell snapshot must record `ui_shell_version`, `ui_shell_snapshot_hash`, and `shell_change_policy`.
8. The Journey Structural Spec must at minimum cover main chain, page map, decision points, CTA hierarchy, container hints, and error/degraded/retry paths.
9. Generate a static HTML prototype with:
   - button responses
   - page-to-page navigation
   - happy path
   - key retry / skip / error journeys
10. Emit structured review artifacts, but do not self-approve human review.
11. Only treat the package as frozen when `python scripts/feat_to_proto.py freeze-guard --artifacts-dir <prototype-package-dir>` succeeds.

## Files To Read

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`

## Default Scripts

- `scripts/validate_input.sh`
- `scripts/validate_output.sh`
- `scripts/freeze_guard.sh`

## Scope Rule

- This workflow produces a reviewable prototype package.
- It must not silently replace human review with AI review.
- It must not claim production-grade implementation semantics.
