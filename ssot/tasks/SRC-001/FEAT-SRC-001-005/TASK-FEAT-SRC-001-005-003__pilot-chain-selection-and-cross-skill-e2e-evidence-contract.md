---
id: TASK-FEAT-SRC-001-005-003
ssot_type: task
title: pilot 主链选择与跨 skill E2E 证据契约
status: frozen
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
  - IMPL-SRC-001-005
historical_note: TASK has been replaced by IMPL in the canonical SSOT chain. This document is retained only for traceability.
version: v2
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260324-v2
parent_id: FEAT-SRC-001-005
derived_from_ids:
- id: FEAT-SRC-001-005
  version: v2
  required: true
source_refs:
- FEAT-SRC-001-005#验收检查
- EPIC-SRC-001-001#范围
- SRC-001#关键约束
owner: qa-engineer
tags:
- planning
- ssot
properties:
  epic_ref: EPIC-SRC-001-001
  src_root_id: src-root-src-001
  task_kind: planning
  workstream: planning
  responsible_role: qa-engineer
  priority: P1
  estimated_effort: 1 day
  acceptance_criteria:
  - FEAT-SRC-001-005/AC-02
  definition_of_done:
  - 选定至少一条真实 producer -> consumer -> audit -> gate pilot 主链，并冻结其 evidence contract。
frozen_at: '2026-03-24T13:30:00+08:00'
---

# Objective

选定至少一条真实 producer -> consumer -> audit -> gate pilot 主链，并冻结其 evidence contract。

# Description

该任务服务于 FEAT-SRC-001-005，负责把该 FEAT 的一段能力边界落成可执行切片，避免实现时重新混层。

## Acceptance Mapping
- FEAT-SRC-001-005/AC-02

## Dependencies
- TASK-FEAT-SRC-001-001-002
- TASK-FEAT-SRC-001-002-002
- TASK-FEAT-SRC-001-003-002
- TASK-FEAT-SRC-001-004-003
- TASK-FEAT-SRC-001-005-001

## Definition Of Done
- 选定至少一条真实 producer -> consumer -> audit -> gate pilot 主链，并冻结其 evidence contract。
- 不与相邻 task 吃职责
- 保留 evidence 与 rollback 说明
