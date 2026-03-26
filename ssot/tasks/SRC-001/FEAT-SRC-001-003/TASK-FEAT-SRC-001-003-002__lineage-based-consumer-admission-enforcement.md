---
id: TASK-FEAT-SRC-001-003-002
ssot_type: task
title: lineage-based consumer admission enforcement
status: frozen
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
  - IMPL-SRC-001-003
historical_note: TASK has been replaced by IMPL in the canonical SSOT chain. This document is retained only for traceability.
version: v2
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260324-v2
parent_id: FEAT-SRC-001-003
derived_from_ids:
- id: FEAT-SRC-001-003
  version: v2
  required: true
source_refs:
- FEAT-SRC-001-003#验收检查
- EPIC-SRC-001-001#范围
- SRC-001#关键约束
owner: runtime-engineer
tags:
- runtime
- ssot
properties:
  epic_ref: EPIC-SRC-001-001
  src_root_id: src-root-src-001
  task_kind: runtime
  workstream: runtime
  responsible_role: runtime-engineer
  priority: P0
  estimated_effort: 1 day
  acceptance_criteria:
  - FEAT-SRC-001-003/AC-01
  - FEAT-SRC-001-003/AC-02
  - FEAT-SRC-001-003/AC-03
  definition_of_done:
  - 实现 lineage-based eligibility、consumer admission 与 no-path-guessing enforcement。
frozen_at: '2026-03-24T13:30:00+08:00'
---

# Objective

实现 lineage-based eligibility、consumer admission 与 no-path-guessing enforcement。

# Description

该任务服务于 FEAT-SRC-001-003，负责把该 FEAT 的一段能力边界落成可执行切片，避免实现时重新混层。

## Acceptance Mapping
- FEAT-SRC-001-003/AC-01
- FEAT-SRC-001-003/AC-02
- FEAT-SRC-001-003/AC-03

## Dependencies
- TASK-FEAT-SRC-001-003-001
- TASK-FEAT-SRC-001-002-001

## Definition Of Done
- 实现 lineage-based eligibility、consumer admission 与 no-path-guessing enforcement。
- 不与相邻 task 吃职责
- 保留 evidence 与 rollback 说明
