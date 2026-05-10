---
id: SRC-FRZ-055
ssot_type: SRC
title: Bug 生命周期管理与 GSD 执行阶段集成
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-frz-055
workflow_key: product.frz-to-src
workflow_run_id: frz-055-extract
source_kind: frz_projection
source_refs:
  - FRZ-055
  - ADR-055
frozen_at: '2026-05-07T14:00:00Z'
---

# Bug 生命周期管理与 GSD 执行阶段集成

## 范围边界

- In scope: Bug 生命周期管理（detected → open → fixing → fixed → re_verify_passed → closed）
- In scope: 终止状态（wont_fix, duplicate, not_reproducible）
- In scope: Gate 与 Bug 注册表集成（gate FAIL → open bug）
- In scope: ll-bug-remediate 技能（生成 bug fix phase）
- In scope: --verify-bugs 再验证机制
- In scope: 影子修复检测（commit hook + registry reconciliation）
- In scope: 与 GSD execute-phase 集成
- Out of scope: 自动修复（LLM 仅辅助，修复由开发者确认）
- Out of scope: Autonomy grant 机制（MVP 阶段所有修复人工确认）
- Out of scope: 6 条件 auto-close（简化为 2 条件 + 通知）
- Out of scope: Break-glass 协议（无 autonomy 门限可绕）

## 用户旅程

### JRN-001: 标准 Bug 修复流程

1. test-run 执行测试，发现失败用例
2. build_bug_bundle 生成 detected 状态 bug，写入 bug registry
3. gate-evaluate 分析，输出 FAIL verdict
4. gate_remediation 将 detected 提升为 open，生成 draft phase
5. 开发者运行 ll-bug-remediate --feat-ref {ref} 确认修复计划
6. 生成 GSD phase（{N}-bug-fix-{bug_id}）
7. 执行 /gsd-execute-phase {N} 完成修复
8. commit 后 status 变为 fixed
9. CI 自动触发 --verify-bugs targeted 验证
10. 验证通过后 status 变为 re_verify_passed
11. 满足 2 条件后系统自动 closed，通知开发者

### JRN-002: 验证失败回退流程

1. test-run 发现失败用例 → detected → gate FAIL → open
2. ll-bug-remediate 生成 phase → 修复代码 → commit → fixed
3. CI 触发 --verify-bugs targeted 验证 → 验证失败
4. status 自动回退到 open
5. 开发者重新分析修复

### JRN-003: 人工终止流程

1. test-run 发现失败用例 → detected
2. 开发者 review 后认为是 wont_fix/duplicate
3. 运行 ll-bug-transition --bug-id {id} --to wont_fix --reason {reason}
4. status 更新为终止状态，审计日志记录

### JRN-004: Gate PASS 归档流程

1. test-run 发现失败用例 → detected
2. settlement 分析认为是环境问题/flaky
3. gate-evaluate 输出 PASS verdict
4. detected bug 自动降级为 archived

## 领域实体

### ENT-001: BugRegistry

- 按 feat 隔离的 Bug 注册表
- 必需字段：bug_id, case_id, coverage_id, status, severity, gap_type

### ENT-002: Bug

- 单条 Bug 记录
- 必需字段：bug_id（唯一标识符）, case_id（关联测试用例 ID）, status（当前状态）

### ENT-003: FixHypothesis

- LLM 生成的修复假设
- 必需字段：root_cause（根因分析）, expected_behavior_change（预期行为变化）

## 状态机

### SM-001: Bug 生命周期状态机

**状态**：detected, open, fixing, fixed, re_verify_passed, closed, wont_fix, duplicate, not_reproducible, archived

**转移**：
- null → detected: test-run 发现用例失败
- detected → open: gate FAIL
- detected → archived: gate PASS
- open → fixing: 开发者开始修复
- open → wont_fix: 开发者人工标记
- open → duplicate: 开发者人工标记
- fixing → fixed: 修复代码已提交
- fixed → re_verify_passed: --verify-bugs 通过
- fixed → open: --verify-bugs 失败
- re_verify_passed → closed: 满足 2 条件自动关闭

## 验收标准

- TC-001: test-run 失败用例应自动生成 detected 状态 bug 写入 registry
- TC-002: gate FAIL 应自动将 detected 提升为 open
- TC-003: gate PASS 应自动将 detected 降级为 archived
- TC-004: ll-bug-remediate 应生成符合 GSD 规范的 bug-fix phase
- 必须验证：gate FAIL → open bug → GSD phase → 修复 → verify → closed 的完整闭环

## 关键约束

- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase

## 开放问题

- UNK-001: 测试层级 not-reproducible 阈值 N 的具体数值（owner: QA治理）
- UNK-002: 影子修复检测 PR check 层的 ROI 评估（owner: 架构）

## 来源追溯

- Source refs: FRZ-055, ADR-055
- 本文件物化自 [src-package.json 与 src-candidate.md
