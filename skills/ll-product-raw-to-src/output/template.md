---
artifact_type: src_candidate
workflow_key: product.raw-to-src
workflow_run_id: raw-to-src-run
title: "{TITLE}"
status: needs_review
source_kind: raw_requirement
source_refs:
  - RAW-INPUT-TODO
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

## 来源追溯

- Source refs: [引用原始来源]
- Input type: [adr/raw_requirement/business_opportunity/business_opportunity_freeze]

## Bridge Context

- 仅当输入是 ADR 时保留本节。
- 需要显式记录 `governed_by_adrs`、`change_scope`、`governance_objects`、`current_failure_modes`、`downstream_inheritance_requirements`、`expected_downstream_objects`、`acceptance_impact`、`non_goals`。
- `change_scope` 不得只是标题复写，必须是治理变更摘要。
