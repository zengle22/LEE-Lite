---
id: IMPL-SRC-001-001
ssot_type: IMPL
title: Mainline Collaboration Loop Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-src-001-001
parent_id: FEAT-SRC-001-001
source_refs:
  - FEAT-SRC-001-001
  - ADR-014
  - ADR-001
  - ADR-003
  - ADR-006
  - ADR-016
  - ARCH-SRC-001-001
  - ARCH-SRC-001-002
  - ARCH-SRC-001-003
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-SRC-001-001
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-001-20260325
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-001-001
  tech_ref: TECH-SRC-001-001
  authority_refs:
    - ADR-014
    - ADR-001
    - ADR-003
    - ADR-006
    - ADR-016
    - ARCH-SRC-001-001
    - ARCH-SRC-001-002
    - ARCH-SRC-001-003
provisional_refs: []
freshness_status: manual_snapshot_requires_rederive_on_upstream_change
rederive_triggers:
  - upstream_ref_version_change
  - acceptance_contract_change
  - ui_api_testset_contract_change
  - touch_set_expands_beyond_declared_scope
repo_discrepancy_status: explicit_discrepancy_handling_required
self_contained_policy: minimum_sufficient_information_not_upstream_mirror
properties:
  feat_ref: FEAT-SRC-001-001
  tech_ref: TECH-SRC-001-001
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: false
  target_template_id: template.dev.feature_delivery_l2
---

# Mainline Collaboration Loop Implementation Task

## 0. Package Semantics

- `package_semantics`: canonical execution package / execution-time single entrypoint
- `authority_scope`: execution input only，不是业务、设计或测试事实源
- `selected_upstream_refs`: 只消费已冻结 `FEAT / TECH / ARCH / ADR` 约束
- `freshness_status`: 上游 ref、验收口径或 touch set 变化时必须重派生或重审
- `repo_discrepancy_status`: repo 现状只能暴露差异，不能静默替代上游冻结真相
- `self_contained_policy`: 收敛执行最小充分信息，不镜像上游全文

## 1. 目标

实现主链 `execution loop -> handoff runtime -> gate pending -> re-entry` 的基础协作链，冻结候选提交、gate pending 可见性与 revise/retry 回流的统一运行时入口。

本次实施不覆盖 formal materialization、formal ref 准入、全局文件治理与 rollout/cutover。

## 2. 上游依赖

- `ADR-001`：双会话双队列闭环
- `ADR-003`：文件化 handoff runtime
- `ADR-006`：gate 外置，不允许 business skill 内嵌最终裁决
- `ADR-016`：第二会话 gate 以 `ll-gate-human-orchestrator` 消费 pending queue
- `ARCH-SRC-001-002`：workflow skill 只写 managed candidate，不写 formal `ssot/*`
- `ARCH-SRC-001-003`：只保留历史 gate materializer 设计动机，不再定义当前 claim/dispatch 模型
- 上游 TECH：`TECH-SRC-001-001`
- 上游 API：`lee gate submit-handoff`、`lee gate show-pending`、`claim-next`

## 3. 实施范围

- 模块范围：
  - `cli/lib/protocol.py`
  - `cli/lib/mainline_runtime.py`
  - `cli/lib/reentry.py`
  - `cli/commands/gate/command.py`
  - `cli/commands/audit/command.py`
- 工程范围：
  - handoff object 持久化
  - gate pending 查询
  - runtime re-entry 写回
  - traceability / evidence 写入
- 不在范围：
  - `capture-decision`
  - `dispatch`
  - formal object / lineage / admission

## 4. 实施步骤

### Step 1

补 `HandoffEnvelope / ProposalEnvelope / ReentryCommand` 协议结构，并定义 `handoff_prepared -> gate_pending` 的状态推进。

完成条件：协议对象和状态枚举稳定，CLI 和 runtime 可共享。

### Step 2

实现 `cli/lib/mainline_runtime.py`，支持 handoff 持久化、queue slot 分配和 trace ref 记录。

完成条件：`lee gate submit-handoff` 能生成 `handoff_ref / queue_slot / gate_pending_ref`。

### Step 3

实现 `cli/lib/reentry.py`，统一 revise/retry 的下一跳选择和回写对象。

完成条件：re-entry 不再由业务 skill 自行拼接。

### Step 4

把 `cli/commands/gate/command.py` 接到 submit/show-pending 两个命令面，并保证第二会话可对 pending 项执行 `claim-next`。

完成条件：CLI 能读取 pending 状态，但不携带 decision 语义。

### Step 5

补运行时测试、evidence 和 smoke subject。

完成条件：至少一条 `submit -> pending -> re-entry` 样例链打通。

## 5. 风险与阻塞

- 若 `ADR-016` 的 pending/claim 语义继续漂移，re-entry 结构可能需要返工。
- 若 candidate 与 formal 对象边界被混用，runtime 可能被误用为 formal carrier。
- 若受治理写入接口未就位，handoff evidence 只能先用受控 staging + managed candidate 方式承接。

## 6. 交付物

- 代码：
  - `cli/lib/mainline_runtime.py`
  - `cli/lib/reentry.py`
  - 协议扩展与 CLI 命令改造
- 测试：
  - submit-handoff happy path
  - pending visibility
  - revise/retry re-entry path
- 证据：
  - execution evidence
  - runtime trace refs
  - smoke gate subject: handoff submit + pending visibility

## 7. 验收检查点

- `lee gate submit-handoff` 只负责提交，不包含 decision 逻辑。
- `lee gate show-pending` 能稳定返回 `pending_state / assigned_gate_queue / trace_ref`。
- pending 项必须能被 `ll-gate-human-orchestrator` 稳定 `claim-next`。
- revise/retry 的回流必须经 `runtime re-entry`，不能由业务 skill 私下改写。
- candidate side 产物只能进入 managed candidate，不得写 formal `ssot/*`。

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 不适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- primary artifact: `impl-task.md` equivalent is this IMPL canonical execution package / execution-time single entrypoint
- supporting refs:
  - `TECH-SRC-001-001`
  - `ARCH-SRC-001-002`
  - `ARCH-SRC-001-003`
  - `ADR-016`
