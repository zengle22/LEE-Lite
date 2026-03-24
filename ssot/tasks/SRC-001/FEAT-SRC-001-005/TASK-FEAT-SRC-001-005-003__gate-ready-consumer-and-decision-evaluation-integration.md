---
id: TASK-FEAT-SRC-001-005-003
ssot_type: task
title: gate-ready Consumer 与决策评估集成
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260324
parent_id: FEAT-SRC-001-005
derived_from_ids:
  - id: FEAT-SRC-001-005
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-005#验收检查
  - FEAT-SRC-001-001#依赖
  - FEAT-SRC-001-004#依赖
owner: workflow-integrator
tags: [external-gate, decision, integration]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: integration
  workstream: workflow-integration
  responsible_role: workflow-integrator
  priority: P0
  milestone: M2-Gate-Decision-Execution
  estimated_effort: 1.5 days
  lifecycle_status: frozen
  implementation_chunks:
    - gate-ready job loading and package completeness checks
    - decision evaluation over evidence, budget, proposal and run-state
    - target matrix validation before materialization handoff
  acceptance_criteria:
    - gate-ready job 能被 external gate consumer 正式消费
    - decision 评估只消费 package completeness、evidence、budget、proposal 与 run-state，不重做业务审查
  definition_of_done:
    - gate-ready consumer 集成完成
    - decision evaluator 能输出唯一 decision_type
  inputs:
    - TASK-FEAT-SRC-001-005-001 gate contract
    - TASK-FEAT-SRC-001-005-002 object schemas
    - gateway and audit evidence
  outputs:
    - gate-ready consumer
    - decision evaluator
frozen_at: '2026-03-24T09:35:00+08:00'
---

# Objective

把 External Gate 接入 gate-ready 队列消费链路，并实现只基于治理结论做判断的 decision evaluator。

# Description

该任务负责让 external gate 不再是附属脚本，而是真正的独立 consumer。它消费 gate-ready job 和标准 package，校验 package completeness、evidence、budget、proposal 与 run-state，然后形成唯一 decision_type。它不能重新做业务语义审查，也不能直接改写上游 candidate package。

## Acceptance Mapping

- FEAT-SRC-001-005 / AC-01: gate decision 必须互斥且可追溯。
- FEAT-SRC-001-005 / AC-03: run closure 与 follow-up dispatch 必须一致。

## Prerequisites

- TASK-FEAT-SRC-001-005-001 与 TASK-FEAT-SRC-001-005-002 已冻结

## Dependencies

- TASK-FEAT-SRC-001-005-001
- TASK-FEAT-SRC-001-005-002
- TASK-FEAT-SRC-001-001-002
- TASK-FEAT-SRC-001-004-002

## Inputs

- external gate input contract 与 decision model
- materialization object schema 与状态推进约束
- Gateway 提供的受管读取 / 写入入口
- Audit 与 supervision 提供的 evidence bundle

## Outputs

- gate-ready consumer
- decision evaluator
- 唯一 gate decision result

## Implementation Chunks

- 消费 gate-ready job，并加载 candidate package、proposal、evidence、budget 与 run-state。
- 依据 decision model 计算唯一 `decision_type`，同时做 target 矩阵校验。
- 将“已决策但未物化”的结果移交给 materialization phase，不在本任务内直接落 formal object。

## Orthogonality Guardrails

- 本任务只负责 decision evaluation，不负责生成或落盘 `materialized-ssot`、`materialized-handoff`、`materialized-job` 与 `run-closure`；这些归 `TASK-FEAT-SRC-001-005-004`。
- 本任务消费 `TASK-FEAT-SRC-001-004-003` 输出的 gate-facing audit mapping，但不重做 audit finding 的解释或 repair targeting。
- 本任务不得吞并 Gateway、Registry 或 Auditor 的领域判断，只能消费它们已经产出的 formal evidence 和 guard result。

## Definition Of Done

- gate-ready job 被 external gate consumer 正式消费
- decision evaluator 能输出 approve / revise / retry / handoff / reject 五类之一
- evaluator 不直接改写 candidate package，且不重做业务语义审查
- 基础验证覆盖 target 约束冲突、证据缺失、budget 违规与 freeze-ready approve 场景

## Observability

```yaml
execution_unit: task
log_scope: gate-decision-execution
audit_fields:
  - run_id
  - task_id
  - feat_id
  - gate_job_ref
  - package_ref
  - decision_type
  - budget_judgement
  - evidence_bundle_refs
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-005-001
  - TASK-FEAT-SRC-001-005-002
  - TASK-FEAT-SRC-001-001-002
  - TASK-FEAT-SRC-001-004-002
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - skills/ll-gate-decision-materializer/scripts/gate_materialize.py
  - src/runtime/gate_ready_consumer.py
fallback: 停用独立 gate-ready consumer，保留对象 contract，不回退为业务 skill 内嵌决策
```
