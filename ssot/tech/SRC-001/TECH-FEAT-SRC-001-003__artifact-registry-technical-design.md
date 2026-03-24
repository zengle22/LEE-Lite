---
id: TECH-FEAT-SRC-001-003
ssot_type: TECH
title: Artifact Identity 与 Registry 正式登记技术设计
status: active
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-003
derived_from_ids:
  - id: FEAT-SRC-001-003
    version: v1
    required: true
source_refs:
  - ARCH-SRC-001-001
  - FEAT-SRC-001-003
  - EPIC-001
  - SRC-001
  - REL-001
  - ADR-005
owner: dev-architecture-owner
tags: [tech, registry, identity, formal-reference, ssot, dev]
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-003
  design_analysis_ref: ssot/tech/SRC-001/T003/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T003/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T003/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T003/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T003/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T003/tech-package.yaml
---

# Artifact Identity 与 Registry 正式登记技术设计

基于 `FEAT-SRC-001-003` 与 `ADR-005`，本技术规格定义 managed artifact 的最小 identity contract、registry record model 和 registry-backed formal reference 解析方式，使正式读取资格判定不再依赖路径猜测，而是依赖受控登记结果。

## Architecture Decisions

### AD-001

- decision: identity contract 仅冻结最小字段集合 `artifact_type + logical_name + stage`
- reason: identity contract 必须足够稳定，才能成为 registry 主键的一部分；`producer_scope` 更适合作为 provenance / registry record 字段，而不是 identity 主键组成
- impact:
  - commit / promote 时必须校验这组字段
  - path、status 与 producer provenance 进入 registry record，而不是进入 identity 本体

### AD-002

- decision: Registry record 记录 `path / producer_run / inputs / status / source_refs / evidence_refs / minimal_lineage`
- reason: 正式读取、审计和后续 materialization 需要依赖记录来解释对象来源与状态
- impact:
  - formal reference 解析必须回到 registry
  - lineage 只保留最小追溯，不承载完整 handoff graph

### AD-003

- decision: Gateway 负责读入口，Registry 负责受管读资格判定与 formal reference 解析
- reason: 若 Gateway 同时负责 eligibility，正式读取逻辑会再次写散；若 Auditor 负责 eligibility，则审计会侵入主链
- impact:
  - managed read path 需要显式 read guard
  - Auditor 和 External Gate 只消费资格判定结果
  - 所有 managed read 都必须经过 Gateway -> Registry guard 链路，不允许出现 path-based 等价正式读取路径

## Feat Mapping

### Goal Mapping

- FEAT clause: 正式产物依赖 registry 中的 identity、path、status 与 source refs 关系  
  TECH response: 定义 registry record model 与 formal reference resolution
- FEAT clause: commit / promote 后完成 identity 绑定、registry 登记与正式读取资格判定  
  TECH response: 设计 binding hook、status transition 和 managed read guard
- FEAT clause: 未进入 registry 的文件不得被正式 skill 消费  
  TECH response: read eligibility guard 必须 fail-closed

### Acceptance Mapping

- acceptance_id: AC-01
  implementation_unit: commit/promote 后生成唯一 identity 并写入 registry
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-003/TASK-FEAT-SRC-001-003-002__registry-binding-and-managed-read-eligibility-enforcement.md
- acceptance_id: AC-02
  implementation_unit: managed read guard 拒绝未注册文件
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-003/TASK-FEAT-SRC-001-003-002__registry-binding-and-managed-read-eligibility-enforcement.md
- acceptance_id: AC-03
  implementation_unit: registry 记录解释 lineage、派生关系与当前状态
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-003/TASK-FEAT-SRC-001-003-001__artifact-minimal-identity-contract-and-registry-schema-definition.md

## Technical Design

### Core Components

- `ArtifactIdentityContract`: 最小 identity 字段模型
- `ArtifactRegistryRecord`: 正式登记对象，包含 path、status、refs、lineage
- `RegistryBindingFlow`: 在 commit/promote 后将合法写入晋升为正式登记对象
- `ManagedReadEligibilityGuard`: 通过 formal reference 和 registry status 判断正式读取资格

### Data Boundaries

- Path Policy 负责目标路径合法性，不进入 registry 主键语义
- Registry 不提供读入口，只做资格判定和 formal reference 解析
- `producer_scope` 若需要表达，只能作为 provenance / registry record 字段出现，不进入 identity contract 主键
- 完整 handoff binding、materialized job 和 run closure 留在 `TECH-FEAT-SRC-001-005`

## Implementation Rules

### Required Inputs

- `FEAT-SRC-001-003`
- `TASK-FEAT-SRC-001-003-001`
- `TASK-FEAT-SRC-001-003-002`
- `TASK-FEAT-SRC-001-001-002`
- `FEAT-SRC-001-002` 提供的合法目标路径

### Required Outputs

- minimal identity contract schema
- registry record schema and status transitions
- registry-backed formal reference and read guard
- provenance fields 与 identity fields 的分层约束

### Forbidden Shortcuts

- 不得依赖裸路径猜测正式身份
- 不得让 Gateway 重写 registry eligibility 判定
- 不得把 `producer_scope`、run id 或 executor 局部切片纳入 identity contract 主键
- 不得把完整 handoff / materialization 图硬塞进本 FEAT 的 lineage 模型

## Delivery Handoffs

- from: `TECH`
  to: `CONTRACT-DESIGN`
  artifacts:
    - identity contract
    - registry record schema
    - formal reference schema
- from: `TECH`
  to: `DEVPLAN`
  artifacts:
    - registry binding hooks
    - managed read guard integration
- from: `TECH`
  to: `TESTPLAN`
  artifacts:
    - unregistered read denial cases
    - lineage traceability cases

## Validation Rules

- rule: identity contract 字段集合必须稳定且必填
  severity: blocker
- rule: 未注册文件不得通过 managed read path
  severity: blocker
- rule: formal reference 解析必须回到 registry record
  severity: major
- rule: 所有 managed read 必须经过 Gateway -> Registry guard，不得存在绕过 Registry 的正式读取路径
  severity: blocker
- rule: lineage 必须能解释 patch/promote/derived 直接来源
  severity: major

## Risks And Fallback

### 风险 1: identity contract 过重

如果将 path、status、producer_scope 或 run-slice 等运行态字段放进 identity contract，会导致 patch/promote 过程出现无必要的 identity 漂移。缓解方式是把 identity 与 record 明确分层。

### 风险 2: 读资格判断重新写散

Gateway、Auditor、External Gate 都可能尝试重做 eligibility。缓解方式是强制所有正式读资格回到 registry-backed guard，并把其他消费者限定为只读结果。

## Out Of Scope

- Path Policy 目录判定
- Workspace diff 审计
- external gate、materialized handoff、materialized job、run closure
