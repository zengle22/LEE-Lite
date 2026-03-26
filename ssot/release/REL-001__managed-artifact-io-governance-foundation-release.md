---
id: REL-001
ssot_type: RELEASE
title: 主链正式交接与治理闭环统一能力 Release
status: accepted
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
- ADR-013
- ADR-014
historical_note: This RELEASE artifact belongs to the earlier release/devplan/testplan world and is no longer an active mainline SSOT object in this repository.
version: v2
schema_version: 0.1.0
release_root_id: release-root-rel-001
workflow_key: workflow.product.task.feat_to_release
source_refs:
- SRC-001
- EPIC-SRC-001-001
- FEAT-SRC-001-001
- FEAT-SRC-001-002
- FEAT-SRC-001-003
- FEAT-SRC-001-004
- FEAT-SRC-001-005
derived_from_ids:
- id: FEAT-SRC-001-001
  version: v2
  required: true
- id: FEAT-SRC-001-002
  version: v2
  required: true
- id: FEAT-SRC-001-003
  version: v2
  required: true
- id: FEAT-SRC-001-004
  version: v2
  required: true
- id: FEAT-SRC-001-005
  version: v2
  required: true
source_freeze_ref: SRC-001
epic_ref: EPIC-SRC-001-001
src_root_id: src-root-src-001
created_at: '2026-03-24T13:30:00+08:00'
owner: product
properties:
  workflow_output_state: release_draft
  release_type: minor
  release_type_taxonomy_status: provisional
  release_type_definition: single-src, single-epic governed mainline release baseline
  release_version: 0.2.0
  release_window:
    kind: planning_window
    start_date: '2026-04-04'
    end_date: '2026-04-10'
    governs: downstream planning boundary
    does_not_mean: go-live approval window
  feat_refs:
  - FEAT-SRC-001-001
  - FEAT-SRC-001-002
  - FEAT-SRC-001-003
  - FEAT-SRC-001-004
  - FEAT-SRC-001-005
  task_bundle_root: ssot/tasks/SRC-001
  task_selection_ref: ssot/release/REL-001/included_tasks.json
  feat_dependency_ref: ssot/release/REL-001/feat_dependency_matrix.json
  validation_result_ref: ssot/release/REL-001/validation_result.json
  dependency_graph_ref: ssot/release/REL-001/dependency_graph.md
  release_scope_ref: ssot/release/REL-001/release_scope.md
---

# 主链正式交接与治理闭环统一能力 Release

## Release Scope
- 覆盖 5 个 FEAT：主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力。
- 仅纳入 included_tasks.json 明列的 13 个 TASK。
- 只冻结 planning baseline，不冻结 dev/test 执行结果或 go-live 决策。

## 冻结语义
- 冻结 feat membership、feat versions、included task manifest 与 dependency matrix。
- 任何上述对象的实质变化都必须新建 REL revision。

## 关键依赖
- FEAT-SRC-001-001 与 FEAT-SRC-001-003 可并行建立基础边界。
- FEAT-SRC-001-002 依赖 FEAT-SRC-001-001 与 FEAT-SRC-001-003。
- FEAT-SRC-001-004 依赖 FEAT-SRC-001-002 与 FEAT-SRC-001-003。
- FEAT-SRC-001-005 依赖前四个 FEAT。
