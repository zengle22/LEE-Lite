---
id: IMPL-FEAT-SRC-001-004
ssot_type: IMPL
title: Mainline Governed IO and Path Integration Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-feat-src-001-004
parent_id: FEAT-SRC-001-004
source_refs:
  - FEAT-SRC-001-004
  - ADR-014
  - ADR-005
  - ADR-006
  - ADR-009
  - ARCH-SRC-001-001
  - ARCH-SRC-001-002
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-004
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-004-20260325
properties:
  feat_ref: FEAT-SRC-001-004
  tech_ref: TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-004
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: false
  target_template_id: template.dev.feature_delivery_l2
---

# Mainline Governed IO and Path Integration Implementation Task

## 1. 目标

把主链 handoff、formal materialization 和 governed skill 正式读写统一接到 ADR-005 的 Gateway / Path Policy / Registry 上，去掉自由写入旁路。

本次实施不扩展成仓库级全局文件治理改造。

## 2. 上游依赖

- `ADR-005`：Gateway / Path Policy / Registry 是受治理写入基础
- `ARCH-SRC-001-002`：candidate governance write 与 formal materialization write 必须分层
- `ADR-006`：formal write 由 gate/control 层发起
- 上游 TECH：`TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-004`
- 上游 API：
  - `lee artifact commit-governed`
  - `lee artifact read-governed`

## 3. 实施范围

- 模块范围：
  - `cli/lib/policy.py`
  - `cli/lib/fs.py`
  - `cli/lib/managed_gateway.py`
  - `cli/lib/registry_store.py`
  - `cli/commands/artifact/command.py`
- 工程范围：
  - governed write preflight
  - managed ref / receipt / registry record
  - read path through managed ref
- 不在范围：
  - 全局文件目录清理
  - consumer admission 决策

## 4. 实施步骤

### Step 1

补 path/mode/overwrite preflight 规则。

完成条件：policy verdict 可独立判断 allow/deny。

### Step 2

实现 `managed_gateway`，串起 preflight、gateway commit、registry bind、receipt build。

完成条件：write/read 都通过统一 adapter 进入治理链。

### Step 3

把 handoff/runtime/formalization 的正式写入切到 `cli/commands/artifact/command.py`。

完成条件：正式写入不再 bypass Gateway。

### Step 4

补失败补偿和 partial success 标记。

完成条件：`policy_deny / registry_prerequisite_failed / receipt_pending` 都有可追溯结果。

## 5. 风险与阻塞

- 旧路径策略若仍被业务 skill 私带，会形成双轨写盘。
- receipt build 与 registry bind 的顺序错误会让 managed ref 成为脏引用。
- compat mode 只能读，若放开 write fallback 会破坏主链约束。

## 6. 交付物

- 代码：
  - `cli/lib/managed_gateway.py`
  - `cli/commands/artifact/command.py`
  - policy/fs/registry 扩展
- 测试：
  - governed write happy path
  - policy deny
  - registry prerequisite fail
  - receipt pending compensation
- 证据：
  - `receipt_ref`
  - `registry_record_ref`
  - managed artifact refs

## 7. 验收检查点

- 正式主链写入必须走 `commit-governed`。
- `policy_deny` 时不得 silent fallback 到自由写入。
- external gate 读取/物化正式对象时只消费 managed artifact ref。
- candidate governance write 与 formal materialization write 必须保持分层。

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 不适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- supporting refs:
  - `TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-004`
  - `ARCH-SRC-001-001`
  - `ARCH-SRC-001-002`
