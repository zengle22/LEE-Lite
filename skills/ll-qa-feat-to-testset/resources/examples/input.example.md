---
artifact_type: feat_freeze_package
workflow_key: product.epic-to-feat
status: accepted
schema_version: 1.0.0
epic_freeze_ref: EPIC-SRC-001-001
src_root_id: SRC-001
source_refs:
  - product.epic-to-feat::feat-src-001
  - FEAT-SRC-001-001
- EPIC-SRC-001-001
  - SRC-001
---

# Example FEAT Freeze Package

## Selected FEAT

- feat_ref: `FEAT-SRC-001-001`
- title: Governed FEAT to TESTSET
- goal: 将 selected FEAT acceptance 拆成受治理 TESTSET candidate package。

## Scope

- 将 acceptance checks 映射为 test_units。
- 输出 analysis、strategy 与 test-set.yaml。
- 生成 gate subjects 与 downstream handoff。

## Constraints

- 只有 `test-set.yaml` 是正式主对象。
- approval 前不得物化为 freeze package。
- gate decision 必须外置且 machine-readable。
