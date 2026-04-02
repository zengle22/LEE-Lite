---
id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002"
ssot_type: FEAT
title: 跨文档一致性与产品行为边界评审流
status: frozen
schema_version: 1.0.0
workflow_key: "product.epic-to-feat"
workflow_run_id: "adr036-src2epic-20260402-r4"
epic_ref: "EPIC-IMPL-IMPLEMENTATION-READINESS"
src_root_id: "SRC-ADR036-RAW2SRC-20260402-R9"
source_refs:
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
candidate_package_ref: "artifacts/epic-to-feat/adr036-src2epic-20260402-r4"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
frozen_at: "2026-04-02T06:54:11.269954+00:00"
---

# 跨文档一致性与产品行为边界评审流

## 目标

冻结 IMPL 与联动 authority 之间的功能逻辑、状态、API、UI、旅程和测试可观测性检查。

## 范围

- functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。
- 冻结 跨文档一致性与产品行为边界评审流 这一独立产品行为切片，并把它保持在产品层边界内。
- 该切片继承 conflict_detection、product_behavior_boundary 的统一约束，但不把 capability axis 直接下沉成实现任务。
- 对外交付 cross-artifact issue inventory，供下游能力直接继承。
- 完成态：关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。

## 输入

- Authoritative EPIC package EPIC-IMPL-IMPLEMENTATION-READINESS
- src_root_id SRC-ADR036-RAW2SRC-20260402-R9
- Inherited scope, constraints, rollout requirements, and acceptance semantics

## 处理

- Translate the parent EPIC product behavior slice into one independently acceptable FEAT with a dedicated product interface, completed state, and boundary statement.
- Preserve parent-child traceability while separating this FEAT's concern from adjacent FEATs and rollout overlays.
- Emit FEAT-specific business flow, deliverable, constraints, and acceptance checks that can seed downstream TECH and TESTSET derivation.

## 输出

- Frozen FEAT product slice for FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002
- FEAT-specific acceptance checks for downstream TECH and TESTSET derivation
- Traceable handoff metadata for downstream governed TECH and TESTSET workflows

## 约束

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 跨文档一致性与产品行为边界评审流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 跨文档一致性与产品行为边界评审流 的完成态必须与“关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 跨文档一致性与产品行为边界评审流 时必须保留 cross-artifact issue inventory 这一 authoritative product deliverable，不能自行改写产品边界。
- 跨文档一致性与产品行为边界评审流 必须继续受 conflict_detection、product_behavior_boundary 的统一约束约束，而不是在下游重新发明同题语义。

## 验收检查

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002-AC-01

- scenario: 跨文档一致性与产品行为边界评审流 happy path reaches the declared completed state
- given: 跨文档一致性与产品行为边界评审流 对应的业务场景已经被触发
- when: 用户或系统沿着 cross-artifact review report 完成该切片要求的关键步骤
- then: 关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002-AC-02

- scenario: 跨文档一致性与产品行为边界评审流 keeps its declared product boundary
- given: 相邻 FEAT 或下游实现尝试把额外能力并入当前切片
- when: 该 FEAT 的业务边界被审查
- then: 该 FEAT 只覆盖“functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002-AC-03

- scenario: 跨文档一致性与产品行为边界评审流 hands downstream one authoritative product deliverable
- given: 下游 TECH 或 TESTSET 需要继承该 FEAT 的产品语义
- when: 跨文档一致性与产品行为边界评审流 被作为 authoritative 输入消费
- then: 下游必须围绕 cross-artifact issue inventory 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。

## 来源追溯

- 物化来源：`artifacts/epic-to-feat/adr036-src2epic-20260402-r4/feat-freeze-bundle.json`
- gate 决策：`artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json`
