---
name: ll-dev-proto-to-ui
description: Governed workflow skill for transforming one approved prototype package into a UI spec package with semantic source ledger and implementation-facing UI contract.
---

# LL Dev Proto to UI

This skill converts one approved `prototype_package` into one governed `ui_spec_package`.

## Runtime Boundary

- Interpret this skill through `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-041-FEAT-to-PROTOTYPE 前增加 Journey ASCII 产物并引入固定 UI Shell 引用基线.MD`.
- This workflow must reject prototype packages that are not human-approved and freeze-ready.
- This workflow must emit a semantic source ledger for UI contract traceability.
- This workflow must treat Journey Structural Spec and UI Shell Snapshot as first-class authorities, not as prototype-only leftovers.
