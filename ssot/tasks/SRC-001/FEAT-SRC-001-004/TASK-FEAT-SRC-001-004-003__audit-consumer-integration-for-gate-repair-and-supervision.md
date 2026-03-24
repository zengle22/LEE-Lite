---
id: TASK-FEAT-SRC-001-004-003
ssot_type: task
title: 审计结果到 gate、repair 与监督链路的集成
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260323
parent_id: FEAT-SRC-001-004
derived_from_ids:
  - id: FEAT-SRC-001-004
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-004#验收检查
  - EPIC-001#拆分原则
  - SRC-001#Bridge Context.acceptance_impact
owner: workflow-integrator
tags: [audit, gate, repair]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: integration
  workstream: workflow-integration
  responsible_role: workflow-integrator
  priority: P1
  milestone: M3-Audit-Consumption
  estimated_effort: 1 day
  lifecycle_status: frozen
  implementation_chunks:
    - audit severity to gate/repair/supervision mapping
    - repair_scope targeting contract
    - qa seed extraction from findings and evidence bundles
  acceptance_criteria:
    - blocker finding 能阻断 gate 或等效推进条件
    - repair 与 supervision 消费 finding 时能定位最小修补范围
  definition_of_done:
    - finding 到 gate/repair/supervision 的消费映射完成
    - 关键路径、开工前置与 QA seed 信息完整
  inputs:
    - TASK-FEAT-SRC-001-004-002 audit findings
    - delivery plan consumption needs
  outputs:
    - gate integration mapping
    - repair and supervision consumption contract
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

把审计 findings 接入 gate、repair 与监督链路，确保违规证据能真正改变推进决策并驱动最小修补。

# Description

该任务关注审计结果的消费侧，而不是 finding 生成本身。它要定义 blocker finding 如何阻断推进、warn/info 如何进入监督与记录、repair 如何根据 repair_scope 做最小修补，以及 QA 如何把风险、依赖和集成点作为 TESTSET seed 消费。目标是让 FEAT-SRC-001-004 的审计能力形成闭环。

## Acceptance Mapping

- FEAT-SRC-001-004 / AC-01: 越权写入 finding 具备明确等级并能进入推进决策。
- FEAT-SRC-001-004 / AC-02: 未注册消费 finding 可作为 blocker 或等效阻断证据。
- FEAT-SRC-001-004 / AC-03: 审计结果足以驱动修补和监督。

## Prerequisites

- TASK-FEAT-SRC-001-004-002 已能生成结构化 findings

## Dependencies

- TASK-FEAT-SRC-001-004-002

## Inputs

- 结构化 findings 与 evidence bundle
- gate、repair、supervision 与 QA 对审计结果的消费边界
- delivery-prep 对关键路径、风险和开工条件的要求

## Outputs

- finding 到 gate/repair/supervision 的映射规则
- QA seed 所需的风险、依赖与集成点清单
- 审计闭环的 entry conditions 与 fallback order

## Implementation Chunks

- 将 blocker / warn / info findings 映射到 gate、repair 与 supervision 的消费边界。
- 提供 repair_scope、object_ref、violation_type 到最小修补动作的 targeting contract。
- 从 findings 与 evidence bundle 中抽取 QA seed 所需风险、依赖与集成点。

## Orthogonality Guardrails

- 本任务只定义审计结果如何被消费，不负责生成 `decision_type`；decision evaluator 归 `TASK-FEAT-SRC-001-005-003`。
- 本任务只提供 gate 可消费的 audit evidence 映射，不负责写出 `gate-decision`、`materialized-job` 或 `run-closure`；这些归 `TASK-FEAT-SRC-001-005-004`。
- 本任务不重复实现 finding 生成；finding 生产仍归 `TASK-FEAT-SRC-001-004-002`。

## Definition Of Done

- blocker/warn/info 到 gate 与 supervision 的消费边界明确
- repair 能根据 repair_scope、object_ref、violation_type 执行最小修补
- QA seed 至少包含 acceptance trace、integration points、risk notes、task lanes
- delivery prep 可从该任务输出中读出关键路径、风险和开工前置

## Observability

```yaml
execution_unit: task
log_scope: audit-consumer-integration
audit_fields:
  - run_id
  - task_id
  - feat_id
  - finding_ref
  - gate_decision
  - repair_scope
  - supervision_ref
  - qa_seed_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-004-002
  - EPIC-001
  - SRC-001
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - integrations/audit_gate_mapping.yaml
  - integrations/audit_repair_contract.yaml
  - integrations/audit_supervision_contract.yaml
preconditions:
  - 先保留当前人工审核与修补入口，避免回滚后中断治理闭环
```
