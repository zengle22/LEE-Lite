---
artifact_type: src_candidate
workflow_key: product.raw-to-src
workflow_run_id: raw-to-src-run
title: "{TITLE}"
status: needs_review
source_kind: raw_requirement
source_refs:
  - RAW-INPUT-TODO
source_snapshot_mode: embedded
---

# {TITLE}

## 问题陈述

[用源输入中的业务问题原文或忠实改写描述问题。]

## 目标用户

- [列出目标用户或受影响角色]

## 触发场景

- [列出触发问题的关键场景]

## 业务动因

- [列出业务驱动、痛点或机会]

## 冻结输入与需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/<run_id>/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- lineage_refs: [列出仅用于追溯的 source refs]
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## Facet Bundle Selection

- facet_inference: [列出 inference 命中的 facet 与证据]
- facet_bundle_recommendation: [列出候选 bundle 与推荐理由]
- selected_facets: [列出 review/gate 选中的最终 facets]
- projector_selection: [列出最终 projector / bundle 选择结果]

## 文档语义层级

- source_layer: [高保真冻结需求层，列出 authoritative fields]
- bridge_layer: [下游兼容投影层，列出 derived fields]
- meta_layer: [追溯与治理元数据层，列出 lineage/compression/inheritance metadata]
- precedence_order: [source_layer, bridge_layer, meta_layer]
- override_rule: [bridge/meta 不得覆盖 source_layer]

## Frozen Contracts

- FC-001: [最高优先级的冻结契约]
- FC-002: [最高优先级的冻结契约]

## 结构化对象契约

- object: [domain_object_name]
  purpose: [对象用途]
  required_fields: [必填字段]
  optional_fields: [选填字段]
  forbidden_fields: [禁止字段]
  completion_effect: [完成后的状态影响]

## 枚举冻结

- field: [enum_field_name]
  semantic_axis: [冻结语义轴]
  allowed_values: [枚举值]
  forbidden_semantics: [禁止语义]
  used_for: [下游用途]

## 治理变更摘要

- [仅当输入是 ADR / governance_bridge_src 时保留本节]
- [概述本次治理变化作用于哪些对象]
- [概述当前失控点与新的统一原则]
- [概述下游必须继承什么，不应误展开什么]

## 关键约束

- [列出已知约束]

## 范围边界

- In scope: [列出本 candidate 负责描述的范围]
- Out of scope: [列出明确非目标]

## 内嵌需求源快照

- Frozen input ref: [run 内冻结的原始输入副本路径]
- Frozen input sha256: [冻结副本 hash]
- Captured at: [冻结时间]
- Original source path: [原始输入路径]
- Embedded source summary: [保证离开外部文件后仍可独立审阅的摘要]

## 来源追溯

- Source refs: [引用原始来源]
- Input type: [adr/raw_requirement/business_opportunity/business_opportunity_freeze]
- SSOT policy: [说明 src 不是仅靠外部引用存活，而是已内嵌并冻结需求源]

## Bridge Context

- 仅当输入是 ADR 时保留本节。
- 需要显式记录 `governed_by_adrs`、`change_scope`、`governance_objects`、`current_failure_modes`、`downstream_inheritance_requirements`、`expected_downstream_objects`、`acceptance_impact`、`non_goals`。
- `change_scope` 不得只是标题复写，必须是治理变更摘要。
