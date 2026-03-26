---
id: TASK-FEAT-SRC-001-002-001
ssot_type: task
title: handoff 与 gate decision 升级链契约定义
status: frozen
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
  - IMPL-FEAT-SRC-001-002
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
- EPIC-001#范围
- SRC-001#关键约束
owner: contract-architect
tags:
- contract
- ssot
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: contract
  workstream: contract
  responsible_role: contract-architect
  priority: P0
  estimated_effort: 1 day
  acceptance_criteria:
  - FEAT-SRC-001-002/AC-01
  - FEAT-SRC-001-002/AC-02
  definition_of_done:
  - 冻结 handoff -> gate decision -> formal materialization 的单一路径契约。
frozen_at: '2026-03-24T13:30:00+08:00'
---

# Objective

冻结 handoff -> gate decision -> formal materialization 的单一路径契约。

# Description

该任务服务于 FEAT-SRC-001-002，负责把该 FEAT 的一段能力边界落成可执行切片，避免实现时重新混层。

## Acceptance Mapping
- FEAT-SRC-001-002/AC-01
- FEAT-SRC-001-002/AC-02

## Dependencies
- TASK-FEAT-SRC-001-001-001
- TASK-FEAT-SRC-001-003-001

## Definition Of Done
- 冻结 handoff -> gate decision -> formal materialization 的单一路径契约。
- 不与相邻 task 吃职责
- 保留 evidence 与 rollback 说明
