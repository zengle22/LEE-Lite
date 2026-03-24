---
id: TECH-FEAT-SRC-001-001
ssot_type: TECH
title: Managed Artifact Gateway 受管操作技术设计
status: active
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-001
derived_from_ids:
  - id: FEAT-SRC-001-001
    version: v1
    required: true
source_refs:
  - ARCH-SRC-001-001
  - FEAT-SRC-001-001
  - EPIC-001
  - SRC-001
  - REL-001
  - ADR-005
owner: dev-architecture-owner
tags: [tech, gateway, managed-artifact, ssot, dev]
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-001
  design_analysis_ref: ssot/tech/SRC-001/T001/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T001/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T001/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T001/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T001/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T001/tech-package.yaml
---

# Managed Artifact Gateway 受管操作技术设计

基于 `FEAT-SRC-001-001`、`SRC-001` 与 `ADR-005`，本技术规格定义 Managed Artifact Gateway 的最小实现形态，使正式读写、commit、promote 与 run-log 追加都经由统一受管入口完成，并为 Path Policy、Registry、Audit 与 External Gate 提供稳定的操作回执。

## Architecture Decisions

### AD-001

- decision: 以单一 Gateway surface 收口 `read_artifact`、`write_artifact`、`commit_artifact`、`promote_artifact`、`append_run_log`
- reason: 正式操作若散落在各 skill 内部，就无法统一执行 fail-closed、回执标准化和后续审计追溯
- impact:
  - runtime 需要一个统一请求归一化层
  - 下游调用方只消费 Gateway 契约，不直接决定物理路径

### AD-002

- decision: Gateway 在运行时必须串联 Path Policy 判定、Registry 绑定调用与标准化 receipt 组装
- reason: Gateway 负责正式操作编排，但不自带政策与身份规则；只有把依赖接入执行链，才能维持职责正交
- impact:
  - 需要 preflight / commit / promote 三类执行钩子
  - receipt 必须包含 policy、registry、staging 与 evidence 引用
  - 所有 managed read 都必须强制委托 Registry-backed formal reference resolution 与 eligibility guard

### AD-003

- decision: Gateway 采用 fail-closed 策略，失败只保留 staging 或 error evidence，不允许 direct write fallback
- reason: 一旦失败路径自动退回自由写入，整个治理面会失效
- impact:
  - 失败分支要显式产出拒绝或错误回执
  - 兼容模式只能保留读能力，不能放开正式写路径

## Feat Mapping

### Goal Mapping

- FEAT clause: 正式 artifact 的读写、提交、晋升与 run-log 追加都通过同一能力面完成  
  TECH response: 定义统一 Gateway dispatcher 和 operation handler family
- FEAT clause: Gateway 成功与失败时输出标准返回对象  
  TECH response: 设计 managed operation receipt / deny receipt / failure evidence 三类结果
- FEAT clause: Gateway 失败不得回退为自由写入  
  TECH response: 在 runtime 层实现 fail-closed write blocking 和 staging retention

### Acceptance Mapping

- acceptance_id: AC-01
  implementation_unit: Gateway dispatcher 接收正式写入请求并输出标准化操作回执
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-001/TASK-FEAT-SRC-001-001-002__gateway-runtime-and-operation-enforcement.md
- acceptance_id: AC-02
  implementation_unit: Gateway failure path 阻断 direct write，并保留 staging 或 error evidence
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-001/TASK-FEAT-SRC-001-001-002__gateway-runtime-and-operation-enforcement.md
- acceptance_id: AC-03
  implementation_unit: 下游 workflow / skill 通过同一 Gateway contract 复用受管操作面
  evidence_ref: ssot/tasks/SRC-001/FEAT-SRC-001-001/TASK-FEAT-SRC-001-001-001__gateway-contract-and-receipt-definition.md

## Technical Design

### Core Components

- `ManagedArtifactGateway`: 正式操作入口，负责请求归一化、handler 路由和执行上下文封装
- `GatewayPreflight`: 调用 Path Policy 与 Registry read/write prerequisites，形成可执行判定
- `OperationHandlers`: 处理 write / read / commit / promote / append_run_log 的差异化动作
- `ManagedReceiptFactory`: 统一生成 success / deny / failure / staging evidence 回执

### Data Boundaries

- Gateway 输入边界只接受 artifact 语义信息、mode、source refs、运行上下文，不直接接受裸路径作为事实来源
- Gateway 输出边界只交付标准化 receipt、staging ref、error evidence 和 formal reference hook，不直接承担审计 finding 生产
- Registry read eligibility 与 formal reference 解析留在 `TECH-FEAT-SRC-001-003`
- `read_artifact` 仍是 Gateway surface，但其 handler 对所有 managed read 都必须强制调用 Registry-backed formal reference resolution 与 eligibility guard，不得存在绕过 Registry 的等价正式读取路径

## Implementation Rules

### Required Inputs

- `FEAT-SRC-001-001`
- `TASK-FEAT-SRC-001-001-001`
- `TASK-FEAT-SRC-001-001-002`
- `FEAT-SRC-001-002` 的 policy verdict
- `FEAT-SRC-001-003` 的 registry binding / read eligibility contract

### Required Outputs

- 统一 Gateway runtime entrypoints
- 标准化 managed operation receipt schema
- fail-closed failure path 与 staging retention

### Forbidden Shortcuts

- 不得让业务 skill 直接决定正式 artifact 物理路径
- 不得在 Gateway 内重写 Path Policy 或 Registry 规则
- 不得在失败路径自动回退为自由写入
- 不得在 Gateway read handler 中通过 path、cache 或本地 binding 绕过 Registry-backed eligibility guard

## Delivery Handoffs

- from: `TECH`
  to: `CONTRACT-DESIGN`
  artifacts:
    - Gateway request / receipt contract
    - Operation handler boundary
- from: `TECH`
  to: `DEVPLAN`
  artifacts:
    - runtime integration slices
    - fail-closed rollout sequence
- from: `TECH`
  to: `TESTPLAN`
  artifacts:
    - managed write happy-path cases
    - deny / failure / staging retention cases

## Validation Rules

- rule: 所有正式写路径必须经由 Gateway
  severity: blocker
- rule: Gateway 失败时不得产生 direct write side effect
  severity: blocker
- rule: policy / registry 结果必须可追溯到 receipt
  severity: major
- rule: 所有 managed read 必须经过 Gateway -> Registry guard 链路
  severity: blocker
- rule: 下游调用面不能出现第二套等价正式写接口
  severity: major

## Risks And Fallback

### 风险 1: Gateway 变成职责黑洞

Path Policy、Registry、Audit 都可能被错误地继续塞进 Gateway。缓解方式是保持 preflight / binding / audit finding 三层边界分离，只允许 Gateway 做编排与回执。

### 风险 2: 兼容期直写旁路残留

历史实现可能继续直接写正式路径。缓解方式是通过 feature flag 切换时默认 fail-closed，兼容模式也只允许读，不允许写旁路。

### 风险 3: managed read 被 facade 化

如果 Gateway 的 read surface 只是薄封装，而底层仍允许 path/cache 直返，未注册对象仍可能被正式消费。缓解方式是把 Registry guard 设为所有 managed read 的强制前置条件。

## Out Of Scope

- Path Policy 规则模型本身
- Registry identity 主键与 read eligibility 逻辑
- 审计 finding 生产与 gate materialization
