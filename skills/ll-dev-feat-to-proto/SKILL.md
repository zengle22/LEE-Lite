---
name: ll-dev-feat-to-proto
description: Governed workflow skill for transforming one frozen FEAT into a static HTML interactive prototype package with complete journey flow, UX button responses, and structured human review gating before UI spec derivation.
---

# LL Dev FEAT to Proto

This skill converts one selected frozen FEAT into one governed `prototype_package`.
The output is a static HTML prototype, not production frontend code.

## Runtime Boundary

- Interpret this skill through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-040-FEAT-to-UI 拆分为 Prototype Freeze 与 UI Spec 派生双阶段基线.MD`.
- This skill stops at experience prototyping and review gating.
- It does not emit final `ui_spec_package`.

## Run Protocol

1. Read `ll.contract.yaml`, `input/contract.yaml`, and `output/contract.yaml`.
2. Accept only one governed `feat_freeze_package` plus an explicit `feat_ref`.
3. `--input` may be either the FEAT package directory or a `formal.feat.*` admission ref.
4. Run `python scripts/feat_to_proto.py run --input <feat-package-dir-or-formal-ref> --feat-ref <feat-ref> --repo-root <repo-root>`.
5. Generate a static HTML prototype with:
   - button responses
   - page-to-page navigation
   - happy path
   - key retry / skip / error journeys
6. Emit structured review artifacts, but do not self-approve human review.
7. Only treat the package as frozen when `python scripts/feat_to_proto.py freeze-guard --artifacts-dir <prototype-package-dir>` succeeds.

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
