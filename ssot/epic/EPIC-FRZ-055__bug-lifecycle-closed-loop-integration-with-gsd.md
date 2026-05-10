---
id: EPIC-FRZ-055
ssot_type: EPIC
title: Bug 生命周期闭环与 GSD 执行阶段集成
status: frozen
version: v1
schema_version: 0.1.0
epic_root_id: epic-root-frz-055
workflow_key: product.src-to-epic.extract
workflow_run_id: extract-frz-055
source_refs:
  - FRZ-055
  - SRC-FRZ-055
  - ADR-055
source_freeze_ref: FRZ-055
src_root_id: src-root-frz-055
frozen_at: '2026-05-07T14:00:00Z'
---

# Bug 生命周期闭环与 GSD 执行阶段集成

## 概述

本 EPIC 将 FRZ-055 的治理问题空间进一步收敛为“Bug 生命周期闭环与 GSD 执行阶段集成”这一 EPIC 级产品能力面，让下游可以围绕稳定的产品行为切片拆分 FEAT，并把 capability axes 保留在 cross-cutting constraints 层。

## 范围

- Journey JRN-001: 标准 Bug 修复流程 — test-run 执行测试，发现失败用例 → build_bug_bundle 生成 detected 状态 bug → gate-evaluate FAIL → open → ll-bug-remediate → GSD phase → 修复 → fixed → verify → re_verify_passed → closed
- Journey JRN-002: 验证失败回退流程
- Journey JRN-003: 人工终止流程
- Journey JRN-004: Gate PASS 归档流程
- 领域实体：BugRegistry, Bug, FixHypothesis
- 状态机：Bug 生命周期状态机（detected → open → fixing → fixed → re_verify_passed → closed, 以及终止状态）
- 验收标准：TC-001 到 TC-004

## 非目标

- 不负责自动修复（LLM 仅辅助，修复由开发者确认）
- 不负责 Autonomy grant 机制（MVP 阶段所有修复人工确认）
- 不负责 6 条件 auto-close（简化为 2 条件 + 通知）
- 不负责 Break-glass 协议（无 autonomy 门限可绕）
- 不解决 UNK-001 和 UNK-002 的开放问题

## 成功标准

- 下游 FEAT 能完整覆盖 4 个用户旅程、3 个实体、1 个状态机
- gate FAIL → open bug → GSD phase → 修复 → verify → closed 的完整闭环可被真实验证
- 三层分离原则（执行层仅记录，验收层仅决策，修复层仅修复）被明确约束
- 按 feat 隔离的 Bug 注册表被明确约束
- ll-bug-remediate 的幂等性被明确约束

## 拆分原则

- 按独立验收能力边界拆分 FEAT，不按实现顺序或单一任务切分
- 每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs
- 建议 FEAT 轴映射：
  - 标准 Bug 修复流程 -> 主闭环能力
  - 验证失败回退流程 -> 回退与重试能力
  - 人工终止与 Gate PASS 归档流程 -> 异常与终止流程
  - Gate 与 Bug 注册表集成 -> gate integration
  - ll-bug-remediate 与 GSD 集成 -> GSD integration

## 约束与依赖

- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase

## 来源追溯

- 本文件物化自 [epic-freeze.json](E:/ai/LEE-Lite-skill-first/artifacts/epic-extract/FRZ-055/epic-freeze.json) 与 [epic-freeze.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-extract/FRZ-055/epic-freeze.md)
