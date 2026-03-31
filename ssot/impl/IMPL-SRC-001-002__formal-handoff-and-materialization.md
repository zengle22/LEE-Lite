---
id: IMPL-SRC-001-002
ssot_type: IMPL
title: Human Gate Orchestrator Decision and Dispatch Implementation
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-src-001-002
parent_id: FEAT-SRC-001-002
source_refs:
  - FEAT-SRC-001-002
  - ADR-014
  - ADR-006
  - ADR-016
  - ADR-005
  - ADR-009
  - ARCH-SRC-001-002
  - ARCH-SRC-001-003
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-SRC-001-002
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-002-20260325
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-001-002
  tech_ref: TECH-SRC-001-002
  authority_refs:
    - ADR-014
    - ADR-006
    - ADR-016
    - ADR-005
    - ADR-009
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
  feat_ref: FEAT-SRC-001-002
  tech_ref: TECH-SRC-001-002
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: false
  target_template_id: template.dev.feature_delivery_l2
  standard_skill_name: ll-gate-human-orchestrator
---

# Human Gate Orchestrator Decision and Dispatch Implementation

## 0. Package Semantics

- `package_semantics`: canonical execution package / execution-time single entrypoint
- `authority_scope`: execution input only，不是业务、设计或测试事实源
- `selected_upstream_refs`: 只消费已冻结 `FEAT / TECH / ARCH / ADR` 约束
- `freshness_status`: 上游 ref、验收口径或 touch set 变化时必须重派生或重审
- `repo_discrepancy_status`: repo 现状只能暴露差异，不能静默替代上游冻结真相
- `self_contained_policy`: 收敛执行最小充分信息，不镜像上游全文

## 1. 目标

实现独立 `ll-gate-human-orchestrator`，负责：

- 唯一 gate decision
- pending gate claim / human decision capture / dispatch
- authoritative decision object 与 dispatch result
- run closure

本次实施不重写业务 candidate 内容，不把 gate 做回业务 skill 内部脚本。

## 2. 上游依赖

- `ADR-016`：第二会话 gate 以 `Human Gate Orchestrator` 为权威基线
- `ADR-006`：保留 external gate 独立于业务 skill、candidate 与 formal 分层等原则
- `ARCH-SRC-001-002`：formal `ssot/*` 只能由 gate/materializer 写入
- `ARCH-SRC-001-003`：仅保留历史设计动机，具体运行模型以 `ADR-016` 为准
- `ADR-005` / `ADR-009`：formal materialization 必须走受治理 Gateway / Registry / Path Policy
- 上游 TECH：`TECH-SRC-001-002`
- 上游 API：
  - `lee gate submit-handoff`
  - `lee gate show-pending`
  - `claim-next`
  - `capture-decision`
  - `dispatch`

## 3. 实施范围

- 模块范围：
  - `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator.py`
  - `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_interaction.py`
  - `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_projection.py`
  - `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_runtime.py`
- 工程范围：
  - gate pending intake、claim、去重与可见性
  - `approve / revise / retry / handoff / reject` 决策持久化
  - decision 后 dispatch 与 run closure
- 不在范围：
  - consumer admission 细则
  - workflow skill candidate 重写

## 4. 实施步骤

### Step 1

实现 `gate-ready package / gate pending / human-decision-request / gate decision / dispatch result / run closure` 协议结构。

完成条件：输入输出对象和状态枚举固定。

### Step 2

实现 `show-pending` 与 `claim-next`，读取 pending gate queue，校验 completeness，生成可供第二会话处理的 decision request。

完成条件：每次 gate claim 都只锁定一个 authoritative pending item，并留下 claim evidence。

### Step 3

实现 `capture-decision`，写出唯一 `approve / revise / retry / handoff / reject` decision。

完成条件：
- revise/retry 写 re-entry 并创建新 run
- handoff 进入 delegated human/special-consumer 分支
- reject 正常 closure

### Step 4

实现 `dispatch`，把 decision 物化为 authoritative downstream result。

完成条件：approve 时能生成 formal publication trigger / downstream ready job / closure evidence；handoff 时能保留 authoritative pending lineage。

### Step 5

实现 `run-closure.json`、partial success 标记与 repair 入口。

完成条件：decision、dispatch、closure 三者可追溯。

## 5. 风险与阻塞

- `handoff` 分支必须保持为 delegated handler，不得偷接自动 approve。
- 若 pending queue / claim 语义继续漂移，第二会话回交会断。
- 若 run lineage 规则未落地，revise/retry 的 child run 追踪会断。

## 6. 交付物

- 代码：
  - queue consumer / interaction / projection / runtime 模块
- 对象：
  - `human-decision-request.json`
  - `gate-decision.json`
  - `dispatch-result.json`
  - `run-closure.json`
- 测试：
  - claim-next path
  - approve path
  - revise/retry path
  - handoff path
  - reject path
  - dispatch fail / closure fail

## 7. 验收检查点

- `approve / revise / retry / handoff / reject` 是唯一合法词表。
- gate pending 必须能被第二会话稳定 `claim-next`。
- gate 正式回交必须经过 `capture-decision` 与 `dispatch`，不得靠路径猜测或口头状态推进。
- approve 之后的 formal publish / downstream enqueue 必须保留 authoritative dispatch evidence，不能伪装成功。
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
  - `ADR-016`
  - `TECH-SRC-001-002`
