---
name: ll-dev-feat-to-ui
description: Deprecated workflow skill. Direct FEAT-to-UI derivation is disabled; use ll-dev-feat-to-proto and ll-dev-proto-to-ui instead.
---

# LL Dev FEAT to UI Deprecated

This skill is deprecated and disabled after ADR-040 and ADR-042.
Do not use it for new runtime invocations.

## Replacement

- Interpret this skill through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-040-FEAT-to-UI 拆分为 Prototype Freeze 与 UI Spec 派生双阶段基线.MD`.
- Also interpret it through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-042-FEAT 与 ARCH-UI-PROTOTYPE 解耦并引入 Surface Map 归属层基线.MD`.
- Replacement path is:
  - `ll-dev-feat-to-surface-map`
  - `ll-dev-feat-to-proto`
  - human review and prototype freeze
  - `ll-dev-proto-to-ui`

## Status

- New dispatch no longer targets this skill.
- Direct CLI invocation returns a deprecation error.
- The deprecation response must explain that UI is a shared design asset and direct FEAT private derivation is blocked.
- `execution.return` no longer routes back into this workflow.
