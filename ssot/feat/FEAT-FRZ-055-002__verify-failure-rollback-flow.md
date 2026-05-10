---
id: FEAT-FRZ-055-002
ssot_type: FEAT
title: 验证失败回退流程
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-frz-055-002
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

# 验证失败回退流程

## 目标

实现验证失败后的回退流程：当 CI 触发 --verify-bugs targeted 验证失败时，bug 状态自动回退到 open，开发者重新分析修复。

## 范围

- test-run 发现失败用例 → detected → gate FAIL → open
- ll-bug-remediate 生成 phase → 修复代码 → commit → fixed
- CI 触发 --verify-bugs targeted 验证 → 验证失败
- status 自动回退到 open
- 开发者重新分析修复

## 验收检查

### AC-01 验证失败自动回退

- scenario: CI 验证失败
- given: fixed 状态 bug，verify 失败
- when: verify 完成
- then: bug status 自动从 fixed 回退到 open

## 约束

- 继承 EPIC-FRZ-055 的所有约束
- 回退时必须保留审计日志

## 来源追溯

- 对应 FRZ-055 JRN-002: 验证失败回退流程
