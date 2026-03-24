---
id: REL-001
ssot_type: RELEASE
title: Managed Artifact IO Governance Foundation Release
status: accepted
version: v1
schema_version: 0.1.0
release_root_id: release-root-rel-001
workflow_key: workflow.product.task.feat_to_release
source_refs:
  - SRC-001
  - EPIC-001
  - FEAT-SRC-001-001
  - FEAT-SRC-001-002
  - FEAT-SRC-001-003
  - FEAT-SRC-001-004
  - FEAT-SRC-001-005
derived_from_ids:
  - id: FEAT-SRC-001-001
    version: v1
    required: true
  - id: FEAT-SRC-001-002
    version: v1
    required: true
  - id: FEAT-SRC-001-003
    version: v1
    required: true
  - id: FEAT-SRC-001-004
    version: v1
    required: true
  - id: FEAT-SRC-001-005
    version: v1
    required: true
source_freeze_ref: SRC-001
epic_ref: EPIC-001
src_root_id: src-root-src-001
created_at: '2026-03-24T10:30:00+08:00'
owner: product
properties:
  workflow_output_state: release_draft
  release_type: minor
  release_type_taxonomy_status: provisional
  release_type_definition: single-src, single-epic governance foundation planning release
  release_version: 0.1.0
  release_window:
    kind: planning_window
    start_date: '2026-03-24'
    end_date: '2026-04-07'
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
  scope_lock_policy:
    freezes:
      - feat scope membership in feat_refs
      - feat versions in derived_from_ids
      - included task manifest selected from listed feat_refs
      - dependency matrix used by downstream planning
    does_not_freeze:
      - downstream devplan or testplan content
      - execution evidence or delivery progress
      - final go-live approval decision
    revision_rule: material scope, feat version, dependency matrix, or included task changes require a new REL revision instead of in-place rewrite
---

# Managed Artifact IO Governance Foundation Release

## 目标

将 `SRC-001` 派生的 Managed Artifact IO 治理能力 FEAT Bundle 组织成一个可被下游 `release-to-devplan` 与 `release-to-testplan` 消费的 RELEASE draft 对象，作为开发计划与测试计划派生前的正式范围载体。

## Release Scope

- 本 RELEASE 覆盖 `FEAT-SRC-001-001` 至 `FEAT-SRC-001-005` 五个 frozen FEAT，以及 `included_tasks.json` 显式列出的 frozen TASK 集合。
- Scope 聚焦 Managed Artifact IO 主链建设：Gateway、Path Policy、Identity / Registry、Runtime Audit、External Gate Decision / Materialization。
- 本 RELEASE 仅组织范围与依赖，不直接冻结 DEVPLAN、TESTPLAN 或具体执行结果。

## 冻结语义

- 本 RELEASE 冻结的是：本次 release scope 的 FEAT 集合、这些 FEAT 的版本、`included_tasks.json` 所定义的 TASK 基线，以及下游规划应继承的依赖矩阵。
- 本 RELEASE 不冻结：DEVPLAN、TESTPLAN、实际执行结果、运行态 evidence、最终 go/no-go 发布裁决。
- 若 FEAT scope、FEAT version、included task 集合或依赖矩阵发生实质变更，必须新建 REL revision，而不是原地改写 `REL-001`。

## 输入基线

- 上游 SRC: `SRC-001`
- 上游 EPIC: `EPIC-001`
- FEAT Bundle:
  - `FEAT-SRC-001-001`
  - `FEAT-SRC-001-002`
  - `FEAT-SRC-001-003`
  - `FEAT-SRC-001-004`
  - `FEAT-SRC-001-005`
- TASK Bundle Root: `ssot/tasks/SRC-001`
- Included Task Manifest: `ssot/release/REL-001/included_tasks.json`

## 计划窗口语义

- `release_window` 在本 RELEASE 中被定义为 `planning_window`，表示下游 `release-to-devplan` 与 `release-to-testplan` 派生时默认继承的目标规划周期。
- 该窗口不是最终上线窗口，也不单独构成 go/no-go 决策承诺。
- 若规划窗口发生影响范围基线的实质变化，应通过新的 REL revision 体现，而不是只修改说明文档。

## Validation Baseline

- `validation_result_ref` 至少校验：`feat_refs` 与 `derived_from_ids` 一致、`included_tasks.json` 仅包含 listed FEAT 派生 TASK、`feat_dependency_matrix.json` 可解且无非法循环交付依赖、`release_scope.md` 与 metadata 一致、`source_refs` / `epic_ref` / `src_root_id` 闭包一致。
- 若上述任一校验失败，本 RELEASE 不应被下游 `release-to-devplan` 或 `release-to-testplan` 当作有效规划基线消费。

## 关键依赖关系

- RELEASE 级依赖以 `feat_dependency_matrix.json` 为准，下游规划应消费其中的 `delivery_depends_on`，而不是把 FEAT 文本中的运行态协作关系直接解释为排期依赖。
- 经过 release planning 归一化后，本 RELEASE 的可解依赖链为：
  - `FEAT-SRC-001-002 -> FEAT-SRC-001-001`
  - `FEAT-SRC-001-001 -> FEAT-SRC-001-003`
  - `FEAT-SRC-001-001/002/003 -> FEAT-SRC-001-004`
  - `FEAT-SRC-001-001/002/003/004 -> FEAT-SRC-001-005`
- `FEAT-SRC-001-001` 与 `FEAT-SRC-001-003` 在 FEAT 文本中存在双向运行态耦合，但在 RELEASE 级被规范化为单向交付依赖，以避免把接口协作误写成循环排期依赖。

## 非目标

- 不在本 RELEASE 内决定 go/no-go 最终发布批准。
- 不在本 RELEASE 内派生 DEVPLAN/TESTPLAN 具体内容。
- 不在本对象内重复展开 FEAT/TASK 的实现细节或代码级设计。

## 状态语义

- `status: accepted` 表示这份 RELEASE draft 已通过当前轮评审，能够作为下游规划输入继续使用。
- `properties.workflow_output_state: release_draft` 仍保留 `feat-to-release` 模板语义，表示它是 release 阶段的规划载体，而不是最终发布批准对象。

## 下游交接

- `release-to-devplan` 应消费本 RELEASE、`feat_dependency_matrix.json` 与 `included_tasks.json`，不得把 `ssot/tasks/SRC-001` 整棵任务树默认视为在 scope 内。
- `release-to-testplan` 应消费本 RELEASE、FEAT acceptance 和 Runtime / Gate 相关约束。

## 来源追溯

- 本 RELEASE 派生自 `SRC-001 -> EPIC-001 -> FEAT-SRC-001-001..005 -> TASK bundle`
- 范围与依赖校验见 `ssot/release/REL-001/dependency_graph.md`
- 范围摘要见 `ssot/release/REL-001/release_scope.md`
- 结构化依赖见 `ssot/release/REL-001/feat_dependency_matrix.json`
- 受控任务纳入清单见 `ssot/release/REL-001/included_tasks.json`
