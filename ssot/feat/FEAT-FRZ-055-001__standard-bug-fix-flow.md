---
id: FEAT-FRZ-055-001
ssot_type: FEAT
title: 标准 Bug 修复流程
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-frz-055-001
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

# 标准 Bug 修复流程

## 目标

实现完整的标准 Bug 修复流程：test-run → detected → gate FAIL → open → ll-bug-remediate → GSD phase → 修复 → fixed → verify → re_verify_passed → closed

## 范围

- test-run 执行测试，发现失败用例
- build_bug_bundle 生成 detected 状态 bug，写入 bug registry
- gate-evaluate 分析，输出 FAIL verdict
- gate_remediation 将 detected 提升为 open，生成 draft phase
- 开发者运行 ll-bug-remediate --feat-ref {ref} 确认修复计划
- 生成 GSD phase（{N}-bug-fix-{bug_id}）
- 执行 /gsd-execute-phase {N} 完成修复
- commit 后 status 变为 fixed
- CI 自动触发 --verify-bugs targeted 验证
- 验证通过后 status 变为 re_verify_passed
- 满足 2 条件后系统自动 closed，通知开发者

## 验收检查

### AC-01 test-run 失败生成 detected

- scenario: test-run 执行测试
- given: 有失败用例
- when: build_bug_bundle 运行
- then: 自动生成 detected 状态 bug 并写入 registry

### AC-02 gate FAIL 提升为 open

- scenario: gate 评估
- given: 有 detected 状态 bug，gate 返回 FAIL
- when: gate_remediation 运行
- then: bug 状态提升为 open，生成 draft phase

### AC-03 ll-bug-remediate 生成 GSD phase

- scenario: 开发者运行 ll-bug-remediate
- given: open 状态 bug
- when: ll-bug-remediate --feat-ref {ref} 运行
- then: 生成符合 GSD 规范的 bug-fix phase

### AC-04 GSD execute-phase 完成修复

- scenario: 执行 GSD phase
- given: 已生成的 bug-fix phase
- when: /gsd-execute-phase {N} 运行
- then: 修复完成，commit 后 status 变为 fixed

### AC-05 CI verify 与自动 close

- scenario: CI 验证流程
- given: fixed 状态 bug
- when: CI 触发 --verify-bugs targeted 验证
- then: 验证通过 → re_verify_passed → 满足 2 条件自动 closed

## 约束

- 继承 EPIC-FRZ-055 的所有约束：三层分离原则、按 feat 隔离、幂等性
- ll-bug-remediate 不得自动执行修复，仅生成 phase 供开发者确认

## 来源追溯

- 本文件物化自 [feat-freeze.json](E:/ai/LEE-Lite-skill-first/artifacts/feat-extract/FRZ-055/feat-freeze.json) 与 [feat-freeze.md](E:/ai/LEE-Lite-skill-first/artifacts/feat-extract/FRZ-055/feat-freeze.md)
- 对应 FRZ-055 JRN-001: 标准 Bug 修复流程
