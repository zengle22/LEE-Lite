---
id: TASK-FEAT-SRC-001-002-002
ssot_type: task
title: formal materialization 与单一路径推进集成
status: frozen
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
  - IMPL-SRC-001-002
historical_note: TASK has been replaced by IMPL in the canonical SSOT chain. This document is retained only for traceability.
version: v2
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260324-v2
parent_id: FEAT-SRC-001-002
derived_from_ids:
- id: FEAT-SRC-001-002
  version: v2
  required: true
source_refs:
- FEAT-SRC-001-002#验收检查
- EPIC-SRC-001-001#范围
- SRC-001#关键约束
owner: workflow-integrator
tags:
- integration
- ssot
properties:
  epic_ref: EPIC-SRC-001-001
  src_root_id: src-root-src-001
  task_kind: integration
  workstream: integration
  responsible_role: workflow-integrator
  priority: P0
  estimated_effort: 1 day
  acceptance_criteria:
  - FEAT-SRC-001-002/AC-01
  - FEAT-SRC-001-002/AC-02
  - FEAT-SRC-001-002/AC-03
  definition_of_done:
  - 把 formalization path、gate result 与 materialization writer 串成单一路径推进。
frozen_at: '2026-03-24T13:30:00+08:00'
---

# Objective

把 formalization path、gate result 与 materialization writer 串成单一路径推进。

# Description

该任务服务于 FEAT-SRC-001-002，负责把该 FEAT 的一段能力边界落成可执行切片，避免实现时重新混层。

## Acceptance Mapping
- FEAT-SRC-001-002/AC-01
- FEAT-SRC-001-002/AC-02
- FEAT-SRC-001-002/AC-03

## Dependencies
- TASK-FEAT-SRC-001-002-001
- TASK-FEAT-SRC-001-004-002

## Definition Of Done
- 把 formalization path、gate result 与 materialization writer 串成单一路径推进。
- 不与相邻 task 吃职责
- 保留 evidence 与 rollback 说明
