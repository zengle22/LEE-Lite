---
id: FEAT-FRZ-055-004
ssot_type: FEAT
title: Gate PASS 归档流程
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-frz-055-004
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

# Gate PASS 归档流程

## 目标

实现 Gate PASS 归档流程：当 settlement 分析认为是环境问题/flaky 时，gate-evaluate 输出 PASS verdict，detected bug 自动降级为 archived。

## 范围

- test-run 发现失败用例 → detected
- settlement 分析认为是环境问题/flaky
- gate-evaluate 输出 PASS verdict
- detected bug 自动降级为 archived

## 验收检查

### AC-01 gate PASS 自动归档

- scenario: gate PASS
- given: detected 状态 bug，settlement 认为是环境问题/flaky，gate 返回 PASS
- when: gate_remediation 运行
- then: bug status 自动从 detected 降级为 archived

## 约束

- 继承 EPIC-FRZ-055 的所有约束
- 必须保留 settlement 分析记录

## 来源追溯

- 对应 FRZ-055 JRN-004: Gate PASS 归档流程
