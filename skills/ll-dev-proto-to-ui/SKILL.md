---
name: ll-dev-proto-to-ui
description: Governed workflow skill for transforming one approved prototype package into a UI spec package with semantic source ledger and implementation-facing UI contract.
---

# LL Dev Proto to UI

This skill converts one approved `prototype_package` into one governed `ui_spec_package`.

## Runtime Boundary

- Interpret this skill through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-040-FEAT-to-UI 拆分为 Prototype Freeze 与 UI Spec 派生双阶段基线.MD`.
- This workflow must reject prototype packages that are not human-approved and freeze-ready.
- This workflow must emit a semantic source ledger for UI contract traceability.
