---
id: TECH-FEAT-SRC-001-002
ssot_type: TECH
title: Path Policy 与写入模式判定技术设计
status: active
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-002
derived_from_ids:
  - id: FEAT-SRC-001-002
    version: v1
    required: true
source_refs:
  - ARCH-SRC-001-001
  - FEAT-SRC-001-002
  - EPIC-001
  - SRC-001
  - REL-001
  - ADR-005
owner: dev-architecture-owner
tags: [tech, path-policy, mode-governance, ssot, dev]
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-002
  design_analysis_ref: ssot/tech/SRC-001/T002/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T002/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T002/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T002/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T002/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T002/tech-package.yaml
---

# Path Policy 与写入模式判定技术设计

基于 `FEAT-SRC-001-002` 与 `ADR-005`，本技术规格定义 Path Policy 的规则模型、mode 判定器和统一 verdict 输出，使 Gateway 与 Auditor 消费同一政策源，而不是各自维护不同的路径、目录和覆盖规则。

## Architecture Decisions

### AD-001

- decision: 将 Path Policy 拆成根目录授权、artifact placement、命名约束和 mode matrix 四层规则
- reason: 路径治理既有静态目录边界，也有随 artifact type 和 mode 变化的动态限制，混成单张表会失去可解释性
- impact:
  - evaluator 需要分层生成 verdict
  - policy bundle 需要支持 artifact type 维度查询

### AD-002

- decision: policy evaluator 输出 machine-readable verdict，包含 allow/deny、reason code、effective path class 和 mode decision
- reason: Gateway、Audit、Repair 必须共享同一政策解释结果，不能靠自由文本传递
- impact:
  - 需要统一 reason code taxonomy
  - verdict 成为 receipt 和 finding 的上游引用

### AD-003

- decision: mode 规则独立于 skill 局部判断，只由 Path Policy 统一裁决
- reason: overwrite、patch、promote 等模式若在 skill 侧临时决定，会直接破坏治理一致性
- impact:
  - 所有正式写请求都必须先经过 mode evaluator
  - 不允许“仅此一次”的隐式例外
  - `promote` 在 mode matrix 中被视为 staging -> managed target 的生命周期跃迁判定，而不是普通覆盖写模式

## Feat Mapping

### Goal Mapping

- FEAT clause: 定义允许写入根目录、禁止区域与路径白名单  
  TECH response: 建立 root authorization layer 和 reserved-zone deny rules
- FEAT clause: 定义 artifact type 到目录映射、命名规则与层级约束  
  TECH response: 建立 placement profile 和 naming validator
- FEAT clause: 为 Gateway 与 Auditor 提供统一判定结果  
  TECH response: 输出共享 policy verdict schema

### Acceptance Mapping

- acceptance_id: AC-01
  implementation_unit: 非法路径命中 deny verdict，并附 reason code
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-002/TASK-FEAT-SRC-001-002-002__path-and-mode-evaluator-implementation.md
- acceptance_id: AC-02
  implementation_unit: mode evaluator 对 artifact type 与 mode 组合给出明确 allow/deny
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-002/TASK-FEAT-SRC-001-002-002__path-and-mode-evaluator-implementation.md
- acceptance_id: AC-03
  implementation_unit: Gateway 与 Auditor 读取同一 policy bundle 和 verdict schema
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-002/TASK-FEAT-SRC-001-002-001__path-policy-rule-model-definition.md

## Technical Design

### Core Components

- `PathPolicyBundle`: 持有 root rules、placement profiles、mode matrix、reason taxonomy
- `PathPlacementEvaluator`: 负责目标路径、命名和层级合法性判断
- `ModeDecisionEvaluator`: 负责 `create/replace/patch/append/promote` 的组合裁决
- `PolicyVerdict`: 为 Gateway、Auditor、Repair 提供统一 verdict 输出

### Data Boundaries

- Path Policy 不负责实际落盘，不生成 registry 记录，也不派发 handoff
- Path Policy 输出的 verdict 必须可以被 receipt 和 audit finding 直接引用
- reserved zone、naming drift、mode conflict 都要有稳定 reason code
- `path class` 至少应覆盖 `managed_target`、`staging`、`reserved_zone`、`illegal_root`、`unmanaged_workspace`

## Implementation Rules

### Required Inputs

- `FEAT-SRC-001-002`
- `TASK-FEAT-SRC-001-002-001`
- `TASK-FEAT-SRC-001-002-002`
- `SRC-001` 冻结的路径治理原则

### Required Outputs

- Path Policy rule model
- shared policy verdict schema
- path + mode evaluator runtime
- `promote` lifecycle verdict，与普通 write mode verdict 分层表达

### Forbidden Shortcuts

- 不得把 policy verdict 退化为自然语言说明
- 不得允许 Gateway 或 Auditor 维护各自的本地白名单
- 不得通过 skill 局部例外覆盖全局 mode 规则
- 不得把 `promote` 简化成普通 `replace` 或 `append`

## Delivery Handoffs

- from: `TECH`
  to: `CONTRACT-DESIGN`
  artifacts:
    - policy bundle schema
    - verdict schema and reason codes
- from: `TECH`
  to: `DEVPLAN`
  artifacts:
    - rule-model implementation sequence
    - evaluator integration points
- from: `TECH`
  to: `TESTPLAN`
  artifacts:
    - illegal root / naming drift cases
    - mode matrix allow/deny matrix cases

## Validation Rules

- rule: 非法 root 和禁止区域必须稳定命中 deny verdict
  severity: blocker
- rule: mode verdict 不得依赖 skill 本地解释
  severity: blocker
- rule: Gateway 与 Auditor 必须消费同一 policy bundle 版本
  severity: major
- rule: verdict 必须输出 reason code 与 path class
  severity: major
- rule: `promote` verdict 必须表达 staging -> managed target 的跃迁合法性
  severity: major

## Risks And Fallback

### 风险 1: 规则粒度过粗

如果 rule model 只表达目录白名单，mode 与命名约束会重新回流到 Gateway 或 skill。缓解方式是从一开始把 placement、naming、mode 拆成可组合层。

### 风险 2: 理由码膨胀

reason code 若无限扩张，会降低下游消费稳定性。缓解方式是将 taxonomy 收敛为 root / naming / mode / reserved-zone 四大类，再做有限扩展。

## Out Of Scope

- 正式写入执行
- registry binding
- Runtime Audit finding 生成
