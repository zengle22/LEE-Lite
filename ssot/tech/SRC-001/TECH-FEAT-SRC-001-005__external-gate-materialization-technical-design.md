---
id: TECH-FEAT-SRC-001-005
ssot_type: TECH
title: External Gate Decision 与正式物化技术设计
status: draft
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-005
derived_from_ids:
  - id: FEAT-SRC-001-005
    version: v1
    required: true
source_refs:
  - ARCH-SRC-001-001
  - FEAT-SRC-001-005
  - EPIC-001
  - SRC-001
  - REL-001
  - ADR-005
  - ADR-006
owner: dev-architecture-owner
tags: [tech, external-gate, materialization, dispatch, ssot, dev]
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  governing_adr_note: ADR-005 is the frozen upstream constraint; ADR-006 is the draft specialization for external gate decision and materialization
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-005
  design_analysis_ref: ssot/tech/SRC-001/T005/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T005/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T005/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T005/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T005/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T005/tech-package.yaml
---

# External Gate Decision 与正式物化技术设计

基于 `FEAT-SRC-001-005`、`REL-001`、`ADR-005` 与 `ADR-006`，本技术规格定义 External Gate 的 decision evaluator、formal materializer、dispatch router 和 run closure writer，使 governed skill 的 candidate package 经过统一 consumer 后，才能形成正式 decision、formal object 和 follow-up execution/human-review 对象。当前版本以 `ADR-005` 作为已冻结治理前置，以 `ADR-006` 作为 draft 中的 external gate 专项细化，因此本 TECH 保持 `draft`，直到 `ADR-006` 冻结或等价规则被并入正式基线。

## Architecture Decisions

### AD-001

- decision: External Gate 采用唯一 `decision_type` 模型，`approve/revise/retry/handoff/reject` 互斥单选
- reason: 多 flag 并列或多结果同时成立会破坏 materialization 和 run closure 的一致性
- impact:
  - gate-ready consumer 需要先完成 package completeness 校验
  - target matrix 必须对每种 decision_type 给出允许字段

### AD-002

- decision: formal object 物化只能发生在 External Gate 内部 consumer，不允许上游 skill 直接落 formal SSOT、handoff 或 job
- reason: proposal 与 formal object 必须分层，否则治理边界会重新散回业务 skill 尾部脚本
- impact:
  - materializer 必须调用 Gateway / Path Policy / Registry 正式链路
  - candidate package 只能携带 proposal，不携带 formal object

### AD-003

- decision: 原 run 被 gate 消费后必须立即写出 run closure，follow-up object 由 decision result 唯一决定
- reason: 若 run closure、dispatch 和 decision 不一致，后续 lineage 与监督链会失真
- impact:
  - 需要 terminal_state、spawned refs、decision ref 三者绑定
  - revise / retry 一律新建 follow-up run / job

## Feat Mapping

### Goal Mapping

- FEAT clause: external gate 定义最小输入集、decision model 与 target 约束矩阵  
  TECH response: 定义 gate-ready package schema、decision evaluator 和 target validator
- FEAT clause: 定义 gate-decision、materialized-ssot、materialized-handoff、materialized-job、run-closure 等对象  
  TECH response: 定义 formal object schema family 和 materialization plan by decision_type
- FEAT clause: formal object 只能在 gate 后物化  
  TECH response: materializer 强制经过 Gateway / Registry 正式链路

### Acceptance Mapping

- acceptance_id: AC-01
  implementation_unit: decision evaluator 输出唯一 decision_type 并满足 target matrix
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-005/TASK-FEAT-SRC-001-005-003__gate-ready-consumer-and-decision-evaluation-integration.md
- acceptance_id: AC-02
  implementation_unit: formal object 由 gate materialization phase 写入，不允许上游 skill 直接生成
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-005/TASK-FEAT-SRC-001-005-004__formal-materialization-and-follow-up-dispatch-integration.md
- acceptance_id: AC-03
  implementation_unit: run closure、spawned refs 与 decision result 保持一致
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-005/TASK-FEAT-SRC-001-005-004__formal-materialization-and-follow-up-dispatch-integration.md

## Technical Design

### Core Components

- `GateReadyConsumer`: 校验 package completeness、acceptance、budget、evidence 前置条件
- `DecisionEvaluator`: 生成唯一 `decision_type` 并验证 target matrix
- `FormalMaterializer`: 按 decision_type 写出 formal object family
- `DispatchRouter`: 派发 follow-up execution job 或 human-review handoff
- `RunClosureWriter`: 将 terminal_state、decision_ref、spawned refs 绑定成最终结案对象

### Data Boundaries

- Audit finding 由 `TECH-FEAT-SRC-001-004` 产生，这里只消费 gate-facing audit mapping
- Registry read eligibility 由 `TECH-FEAT-SRC-001-003` 负责，这里只消费 formal reference 和 registry constraint
- External Gate 不重新生成或改写业务内容本体，但可以基于 gate-ready package 中的 acceptance、evidence、audit 映射与 target constraints 做通过性与去向判定

## Implementation Rules

### Required Inputs

- `FEAT-SRC-001-005`
- `TASK-FEAT-SRC-001-005-001`
- `TASK-FEAT-SRC-001-005-002`
- `TASK-FEAT-SRC-001-005-003`
- `TASK-FEAT-SRC-001-005-004`
- `ADR-006`

### Required Outputs

- gate-ready package schema
- unique decision evaluator and target matrix validator
- formal materialization plan and run closure writer
- ADR-005 governance constraints 与 ADR-006 external gate specialization 的关系说明

### Forbidden Shortcuts

- 不得在上游 skill 中直接写 formal SSOT、formal handoff、formal job
- 不得让 materializer 重新评估业务语义或重写审计 taxonomy
- 不得让原 run 在 gate 后继续保持开放态
- 在 `ADR-006` 仍为 draft 时，不得将本 TECH 视为已完成 contract-design 准入的 active 基线

## Delivery Handoffs

- from: `TECH`
  to: `CONTRACT-DESIGN`
  artifacts:
    - gate-ready package schema
    - decision_type matrix
    - formal object schemas
- from: `TECH`
  to: `DEVPLAN`
  artifacts:
    - evaluator / materializer / dispatch slices
    - queue routing and closure sequencing
- from: `TECH`
  to: `TESTPLAN`
  artifacts:
    - mutually-exclusive decision cases
    - formal object per decision_type cases
    - run closure consistency cases

## Validation Rules

- rule: `decision_type` 必须互斥单选
  severity: blocker
- rule: formal object 只能在 gate 后写入正式链路
  severity: blocker
- rule: 原 run 被 gate 消费后必须进入终态
  severity: blocker
- rule: spawned refs 与 terminal_state 必须和 decision 结果一致
  severity: major

## Risks And Fallback

### 风险 1: decision 与物化脱节

若 evaluator 和 materializer 分别维护自己的状态机，很容易出现 decision 正确但 formal object 错配。缓解方式是以 decision_type 为唯一主键，生成单一 materialization plan。

### 风险 2: external gate 回落为 skill 尾部脚本

一旦 formal object 又由业务 skill 直接写出，独立 gate 能力面会失效。缓解方式是把 materialization 和 run closure writer 固定为独立 consumer/skill。

### 风险 3: 上游 ADR 基线未冻结

当前 `ADR-006` 仍为 draft，若直接把本 TECH 当作 active 基线，会导致 external gate 的 decision 与 materialization 语义建立在未冻结前置之上。缓解方式是在 `ADR-006` 冻结前保持本 TECH 为 `draft`，并明确 `ADR-005` 只是基础约束而非完整 external gate 专项规则。

## Out Of Scope

- 上游业务语义评审
- 人类审批责任替代
- 重型 runtime 基础设施要求
