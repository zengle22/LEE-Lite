---
name: ll-dev-feat-to-ui
description: Governed workflow skill for transforming one frozen FEAT into a UI Spec package that freezes user path, ASCII structure, state model, and UI/TECH boundary before implementation.
---

# LL Dev FEAT to UI

This skill converts one selected frozen FEAT into one governed `ui_spec_package`. The output is not a visual mockup or page code. It is an interface-layer contract that makes user path, page structure, state handling, and UI/TECH boundaries explicit enough for downstream development.

## Run Protocol

1. Read `ll.contract.yaml`, `input/contract.yaml`, and `output/contract.yaml`.
2. Accept only a governed `feat_freeze_package` plus an explicit `feat_ref`.
3. Run `python scripts/feat_to_ui.py run --input <feat-package-dir> --feat-ref <feat-ref> --repo-root <repo-root>`.
4. Convert FEAT semantics into UI unit scope, user path, ASCII wireframe, state model, and technical boundaries.
5. Always emit a `UI Spec Completeness Check` result with `pass | conditional_pass | fail`.
6. Only treat the package as ready when `python scripts/feat_to_ui.py freeze-guard --artifacts-dir <ui-package-dir>` succeeds.


## Role Split

- Executor responsibilities live in `agents/executor.md`.
- Supervisor responsibilities live in `agents/supervisor.md`.
- The executor must not issue the final semantic pass on its own output.

## Important Scope Rule

- This workflow stops at `FEAT -> UI Spec`.
- It does not include later体验优化、验收、编码或测试执行流程。
- UI Spec is the interface-layer SSOT, not a visual design draft and not a code design package.

## Files To Read

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Default Scripts

- `scripts/validate_input.sh`
- `scripts/validate_output.sh`
- `scripts/collect_evidence.sh`
- `scripts/freeze_guard.sh`

## Current Rollout Note

This repository now includes a runnable governed `feat-to-ui` skill, but FEAT mainline dispatch is not auto-wired by default yet. The current FEAT contract does not reliably carry an explicit `ui_required` signal for every FEAT, so automatic dispatch would force UI derivation onto backend-only capabilities.
