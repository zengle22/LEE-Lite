---
id: TASK-FEAT-SRC-001-004-002
ssot_type: task
title: Workspace Auditor 与结构化 finding 生成实现
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
  - FEAT-SRC-001-001#依赖
  - FEAT-SRC-001-002#依赖
  - FEAT-SRC-001-003#依赖
owner: runtime-engineer
tags: [audit, workspace, findings]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: implementation
  workstream: runtime-implementation
  responsible_role: runtime-engineer
  priority: P0
  milestone: M2-Audit-Execution
  estimated_effort: 1.5 days
  lifecycle_status: frozen
  acceptance_criteria:
    - 执行前后 workspace diff 与 IO Contract 对比可生成结构化 findings
    - 越权写入、未注册消费、路径漂移与命名违规可被识别
  definition_of_done:
    - workspace auditor 实现完成
    - finding 输出可直接驱动 gate 和 repair
  inputs:
    - TASK-FEAT-SRC-001-004-001 audit schemas
    - gateway receipts
    - path policy decisions
    - registry records
  outputs:
    - workspace auditor
    - structured audit findings
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

实现 Workspace Auditor，在 skill 执行前后生成可消费的结构化 findings，而不是停留在目录 diff 或自然语言报告。

# Description

该任务负责把 IO Contract、Path Policy、Gateway 回执和 Registry 记录综合起来，对运行期实际行为做审计。它要能识别绕过 Gateway 的正式写入、未注册文件消费、越界路径写入、命名漂移和 contract 外访问，并将结果输出为 blocker/warn/info 分级的 finding 集合。

## Acceptance Mapping

- FEAT-SRC-001-004 / AC-01: 越权写入必须可见。
- FEAT-SRC-001-004 / AC-02: 未注册 artifact 消费必须被识别。
- FEAT-SRC-001-004 / AC-03: 审计结果必须能驱动修补。

## Prerequisites

- TASK-FEAT-SRC-001-004-001 已冻结
- Gateway、Path Policy、Registry 基础能力可产出追溯对象

## Dependencies

- TASK-FEAT-SRC-001-001-002
- TASK-FEAT-SRC-001-002-002
- TASK-FEAT-SRC-001-003-002
- TASK-FEAT-SRC-001-004-001

## Inputs

- IO Contract 与 finding schema
- 执行前后 workspace 快照
- Gateway 回执、Path Policy 判定和 Registry 记录

## Outputs

- Workspace Auditor 实现
- 结构化 findings 集
- 供 repair/gate/supervision 复用的证据对象

## Definition Of Done

- auditor 同时比较 contract scope、路径政策和 registry 状态
- 能识别 direct write bypass、registry miss、path violation、naming drift
- findings 包含 severity、object_ref、evidence_refs、repair_scope
- 自动化验证覆盖 blocker 与 non-blocker 典型场景

## Observability

```yaml
execution_unit: task
log_scope: workspace-audit-execution
audit_fields:
  - run_id
  - task_id
  - feat_id
  - contract_ref
  - scanned_path_count
  - finding_count
  - blocker_count
  - evidence_bundle_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-001-002
  - TASK-FEAT-SRC-001-002-002
  - TASK-FEAT-SRC-001-003-002
  - TASK-FEAT-SRC-001-004-001
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - src/runtime/workspace_auditor.py
  - src/runtime/audit_finding_builder.py
fallback: 仅保留只读审计日志输出，不将结果接入阻断链路
```
