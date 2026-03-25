---
id: IMPL-FEAT-SRC-001-002
ssot_type: IMPL
title: External Gate Decision and Formal Materialization Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-feat-src-001-002
parent_id: FEAT-SRC-001-002
source_refs:
  - FEAT-SRC-001-002
  - ADR-014
  - ADR-006
  - ADR-005
  - ADR-009
  - ARCH-SRC-001-002
  - ARCH-SRC-001-003
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-002
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-002-20260325
properties:
  feat_ref: FEAT-SRC-001-002
  tech_ref: TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-002
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: false
  target_template_id: template.dev.feature_delivery_l2
  standard_skill_name: ll-gate-decision-materializer
---

# External Gate Decision and Formal Materialization Implementation Task

## 1. 目标

实现独立 `ll-gate-decision-materializer`，负责：

- 唯一 gate decision
- formal object materialization
- materialized handoff/job
- run closure

本次实施不重写业务 candidate 内容，不把 gate 做回业务 skill 内部脚本。

## 2. 上游依赖

- `ADR-006`：external gate 是独立 skill/consumer
- `ARCH-SRC-001-002`：formal `ssot/*` 只能由 gate/materializer 写入
- `ARCH-SRC-001-003`：gate skill 组件设计与状态机
- `ADR-005` / `ADR-009`：formal materialization 必须走受治理 Gateway / Registry / Path Policy
- 上游 TECH：`TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-002`
- 上游 API：
  - `lee gate decide`
  - `lee registry publish-formal`

## 3. 实施范围

- 模块范围：
  - `cli/lib/gate_protocol.py`
  - `cli/lib/gate_reader.py`
  - `cli/lib/gate_decision.py`
  - `cli/lib/gate_materializer.py`
  - `cli/lib/gate_closure.py`
  - `cli/lib/formalization.py`
  - `cli/lib/registry_store.py`
  - `cli/commands/gate/command.py`
  - `cli/commands/registry/command.py`
- 工程范围：
  - decision object 持久化
  - approve/revise/retry/handoff/reject 分支
  - formal object / materialized handoff / materialized job / run closure
- 不在范围：
  - consumer admission 细则
  - workflow skill candidate 重写

## 4. 实施步骤

### Step 1

实现 `GateReadyPackage / GateDecision / FormalMaterializationRequest / RunClosure` 协议结构。

完成条件：输入输出对象和状态枚举固定。

### Step 2

实现 `lee gate decide`，读取 gate-ready package，校验 completeness，写 `gate-decision.json`。

完成条件：每次 gate 消费都产出唯一 decision。

### Step 3

实现 `revise / retry / handoff / reject` 分支。

完成条件：
- revise/retry 写 re-entry 并创建新 run
- handoff 物化 `materialized-handoff.json` 和 delegated job
- reject 正常 closure

### Step 4

实现 `lee registry publish-formal` 和 `gate_materializer`。

完成条件：approve 时能生成 formal object、formal ref、lineage、receipt。

### Step 5

实现 `run-closure.json`、partial success 标记与 repair 入口。

完成条件：decision、materialization、closure 三者可追溯。

## 5. 风险与阻塞

- `handoff` 分支必须保持为 delegated handler，不得偷接 formal publish。
- 若 Gateway / Registry 接口未稳定，formal SSOT 物化不能放开。
- 若 run lineage 规则未落地，revise/retry 的 child run 追踪会断。

## 6. 交付物

- 代码：
  - gate reader / decision / materializer / closure 模块
  - `cli/commands/gate/command.py`
  - `cli/commands/registry/command.py`
- 对象：
  - `gate-decision.json`
  - `materialized-ssot.json`
  - `materialized-handoff.json`
  - `materialized-job.json`
  - `run-closure.json`
- 测试：
  - approve path
  - revise/retry path
  - handoff path
  - reject path
  - materialization fail / publish fail / registry bind fail

## 7. 验收检查点

- `approve / revise / retry / handoff / reject` 是唯一合法词表。
- gate 是唯一 formal `ssot/*` 写入入口。
- formal SSOT 写入必须服从 `ARCH-SRC-001-002` 的 `decision -> formal materialization -> ssot` 链。
- materialization 成功但 publish 失败时必须进入 `publish_pending`，不能伪装成功。
- business skill 仍只产出 candidate/proposal/evidence。

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 不适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- supporting refs:
  - `ARCH-SRC-001-002`
  - `ARCH-SRC-001-003`
  - `TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-002`
