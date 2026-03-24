---
id: TECH-FEAT-SRC-001-004
ssot_type: TECH
title: Runtime Audit 与 IO Contract 执行技术设计
status: active
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-004
derived_from_ids:
  - id: FEAT-SRC-001-004
    version: v1
    required: true
source_refs:
  - ARCH-SRC-001-001
  - FEAT-SRC-001-004
  - EPIC-001
  - SRC-001
  - REL-001
  - ADR-005
owner: dev-architecture-owner
tags: [tech, audit, io-contract, evidence, ssot, dev]
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-004
  design_analysis_ref: ssot/tech/SRC-001/T004/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T004/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T004/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T004/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T004/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T004/tech-package.yaml
---

# Runtime Audit 与 IO Contract 执行技术设计

基于 `FEAT-SRC-001-004` 与 `ADR-005`，本技术规格定义 IO Contract、workspace diff 审计器、finding 分级和 audit consumer 映射，使运行期越权写入、未注册消费和路径漂移都能被转化为 gate、repair 与 supervision 可直接消费的结构化证据。

## Architecture Decisions

### AD-001

- decision: IO Contract 至少拆成 artifact scope、path scope、operation scope、staging promotion 四个边界面
- reason: 只检查目录 diff 无法解释“这个动作是否被允许”，必须先有 contract 语义边界
- impact:
  - executor 需要在运行前声明 contract
  - auditor 需要把 contract 与 runtime records 联合求值

### AD-002

- decision: Workspace Auditor 联合消费 workspace diff、Gateway receipts、Path Policy verdicts 和 Registry records
- reason: 审计只看文件变更会误判正常 staging，也无法确认是否存在绕过 managed read path 的未注册消费旁路
- impact:
  - finding 生成器需要支持多源 evidence join
  - diff 只是证据入口，不是最终裁决依据

### AD-003

- decision: finding 输出 blocker / warn / info，并包含 repair targeting 所需定位字段
- reason: finding 若只停留在自然语言描述，就无法驱动 repair 和 gate consumer
- impact:
  - 需要标准化 finding schema
  - gate、repair 和 supervision 只消费 finding 与 consumer-facing mapping contract，不重写 severity taxonomy

## Feat Mapping

### Goal Mapping

- FEAT clause: 识别越权写入、未注册 artifact、contract 外访问与路径漂移  
  TECH response: 联合求值 contract + runtime evidence，输出结构化 findings，其中未注册消费以“旁路或尝试证据”形式被捕获
- FEAT clause: 为 executor、supervisor、gate 与 repair 提供可消费证据  
  TECH response: 设计 audit report 和 consumer-facing finding schema
- FEAT clause: 审计结果必须能进入最小修补闭环  
  TECH response: finding 必须携带 object_ref、violation_type、minimal_patch_scope

### Acceptance Mapping

- acceptance_id: AC-01
  implementation_unit: contract 外写入被转化为带等级的 audit finding
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-004/TASK-FEAT-SRC-001-004-002__workspace-auditor-and-finding-generation.md
- acceptance_id: AC-02
  implementation_unit: bypassed or attempted unmanaged consumption 生成 blocker 或等效阻断 finding
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-004/TASK-FEAT-SRC-001-004-002__workspace-auditor-and-finding-generation.md
- acceptance_id: AC-03
  implementation_unit: finding 可被 repair / gate / supervision 消费并定位最小修补范围
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-004/TASK-FEAT-SRC-001-004-003__audit-consumer-integration-for-gate-repair-and-supervision.md

## Technical Design

### Core Components

- `IOContractModel`: 运行前声明 artifact/path/operation/staging 范围
- `WorkspaceAuditor`: 采集前后快照差异并联合 runtime records 求值
- `FindingClassifier`: 产出 severity、violation_type、evidence refs、patch scope
- `AuditConsumerMappingContract`: 为 repair、gate、supervision 暴露统一 finding 消费映射；实际投递由 orchestration / handoff 层承担

### Data Boundaries

- 主防线是 Gateway + Registry guard 在读时阻断未注册消费；审计负责识别绕过 managed read path 的旁路消费或消费尝试证据
- 审计不替代 Gateway 正式写入和 Registry eligibility 判定
- gate consumer 只消费 findings，不负责重新解释 severity
- repair 只消费定位信息，不负责回写审计 taxonomy

## Implementation Rules

### Required Inputs

- `FEAT-SRC-001-004`
- `TASK-FEAT-SRC-001-004-001`
- `TASK-FEAT-SRC-001-004-002`
- `TASK-FEAT-SRC-001-004-003`
- Gateway receipts、policy verdicts、registry records、workspace diff

### Required Outputs

- IO Contract schema
- structured audit finding schema
- audit consumer mapping contract
- bypass / attempted unmanaged consumption evidence model

### Forbidden Shortcuts

- 不得把 workspace diff 直接当作最终违规结论
- 不得把 gate decision 或 repair strategy 写回 auditor
- 不得生成无法定位对象和修补范围的自然语言 findings
- 不得把 Auditor 实现成消息总线或正式读取阻断器

## Delivery Handoffs

- from: `TECH`
  to: `CONTRACT-DESIGN`
  artifacts:
    - IO Contract schema
    - finding schema and severity model
- from: `TECH`
  to: `DEVPLAN`
  artifacts:
    - diff collector and evidence join slices
    - consumer mapping integration points
- from: `TECH`
  to: `TESTPLAN`
  artifacts:
    - unauthorized write cases
    - unmanaged read cases
    - repair targeting cases

## Validation Rules

- rule: 绕过 Gateway 的正式写入必须可见
  severity: blocker
- rule: 未注册 artifact 消费必须形成 blocker 或等效阻断证据
  severity: blocker
- rule: 审计对未注册消费的职责仅限于旁路或尝试证据识别，不替代 Gateway -> Registry guard 主防线
  severity: blocker
- rule: finding 必须可定位最小修补范围
  severity: major
- rule: gate / repair / supervision 消费同一 finding schema
  severity: major

## Risks And Fallback

### 风险 1: 审计信号噪声过高

如果 staging、临时目录和正式路径没有清楚区分，auditor 会产生大量误报。缓解方式是在 contract 中显式声明 staging promotion 规则，并在 policy verdict 中标记 path class。

### 风险 2: consumer 侵占 auditor 职责

gate 或 repair 若重新解释 finding，会导致三套 severity 语义。缓解方式是将 finding schema 视为唯一证据源，消费者只能派生动作，不能重写原始判断。

## Out Of Scope

- 正式 artifact 写入执行
- Registry formal reference 解析
- External Gate decision model 与 formal materialization
