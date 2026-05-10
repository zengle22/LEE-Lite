---
id: FEAT-FRZ-055-003
ssot_type: FEAT
title: 人工终止流程
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-frz-055-003
workflow_key: product.epic-to-feat.extract
workflow_run_id: extract-frz-055
source_refs:
  - EPIC-FRZ-055
  - SRC-FRZ-055
  - FRZ-055
  - ADR-055
epic_ref: EPIC-FRZ-055
epic_root_id: epic-root-frz-055
source_freeze_ref: FRZ-055
src_root_id: src-root-frz-055
frozen_at: '2026-05-07T14:00:00Z'
---

# 人工终止流程

## 目标

实现人工终止流程：开发者 review 后认为是 wont_fix/duplicate/not_reproducible，通过 ll-bug-transition 命令更新状态。

## 范围

- test-run 发现失败用例 → detected
- 开发者 review 后认为是 wont_fix/duplicate
- 运行 ll-bug-transition --bug-id {id} --to wont_fix --reason {reason}
- status 更新为终止状态，审计日志记录

## 验收检查

### AC-01 ll-bug-transition 命令

- scenario: 开发者终止 bug
- given: detected/open 状态 bug
- when: ll-bug-transition --bug-id {id} --to {wont_fix/duplicate/not_reproducible} --reason {reason} 运行
- then: bug status 更新为指定终止状态，审计日志记录

## 约束

- 继承 EPIC-FRZ-055 的所有约束
- 终止状态：wont_fix, duplicate, not_reproducible
- 必须提供 reason 参数，记录审计日志

## 来源追溯

- 对应 FRZ-055 JRN-003: 人工终止流程
