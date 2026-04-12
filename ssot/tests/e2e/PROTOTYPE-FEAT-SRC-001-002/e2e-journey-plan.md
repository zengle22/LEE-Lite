# E2E Journey Plan — FEAT-SRC-001-002 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-001-002 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-001-002__formal-handoff-and-materialization.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-001-002 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 开发者发起 handoff 升级 -> 系统执行 gate decision -> 生成 formal materialization -> 开发者确认单一路径完成 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 开发者尝试用 candidate 绕过 gate 直接作为 formal input -> 系统拒绝并返回旁路阻断错误 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 业务 skill 尝试接收 formalization decision 产生回流 -> 系统拒绝并返回防回流错误 |
| 4 | JOURNEY-RETRY-001 | retry | P1 | 开发者检测下游 decision 语义不合规 -> 修正为统一语义后重新验证 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 正式升级路径

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至正式升级验证入口 | 系统显示升级配置界面 |
| 2 | 开发者选择 handoff 对象 | 系统校验 handoff 状态和 gate decision 存在 |
| 3 | 开发者发起升级请求 | 系统执行单一路径: handoff -> gate decision -> formal materialization |
| 4 | 系统生成 formal materialization | 开发者看到升级成功确认 |
| 5 | 开发者验证无并行 shortcut | 系统显示唯一路径证明 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 旁路阻断

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者尝试将 candidate 直接指定为 downstream formal input | 系统检测旁路企图 |
| 2 | 系统返回 GATE_BYPASS_BLOCKED 错误 | 开发者看到错误详情和正确的升级路径 |
| 3 | 开发者改为通过正式 gate 流程提交 | 系统接受并进入主旅程步骤 2 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 防回流

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 业务 skill 尝试接收并处理 formalization decision | 系统检测回流企图 |
| 2 | 系统返回 FORMAL_REFLOW_BLOCKED 错误 | 开发者看到错误和职责分离说明 |
| 3 | 开发者将 formalization 转移到业务 skill 之外 | 系统接受 |

#### JOURNEY-RETRY-001: 重试旅程 — 语义不合规

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 下游 workflow 使用非标准 decision 语义 | 系统检测语义偏差 |
| 2 | 系统返回 PARALLEL_SEMANTIC 错误 | 开发者看到偏差详情 |
| 3 | 开发者修正为标准 approve/revise/retry/handoff/reject 语义 | 系统验证通过 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次升级验证流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
