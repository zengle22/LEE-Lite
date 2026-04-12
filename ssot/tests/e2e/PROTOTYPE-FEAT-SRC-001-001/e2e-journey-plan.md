# E2E Journey Plan — FEAT-SRC-001-001 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-001-001 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-001-001__mainline-collaboration-loop.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-001-001 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 开发者提交 execution loop 对象 -> 系统生成 handoff -> 进入 gate-human 交接 -> 开发者查看责任分离验证结果 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 开发者尝试在无效 loop 状态下提交 -> 系统拒绝并返回状态错误 -> 开发者修正状态后重新提交 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 开发者尝试回流但目标 loop 不允许重入 -> 系统拒绝并返回回流边界错误 -> 开发者检查状态后修正 |
| 4 | JOURNEY-RETRY-001 | retry | P1 | 下游 workflow 创建平行 handoff 规则 -> 系统检测到违规 -> 开发者修正为继承模式后重新验证 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 完整协作闭环

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至 loop 协作验证入口 | 系统显示协作配置界面 |
| 2 | 开发者配置 execution loop 提交参数 | 系统实时校验 loop 状态和对象引用 |
| 3 | 开发者提交 execution loop 对象 | 系统校验并通过 gate loop 接收 |
| 4 | 系统执行 gate-human 交接 | 开发者看到交接成功确认 |
| 5 | 系统验证 loop 责任分离 | 开发者看到无重叠验证通过 |
| 6 | 开发者查看协作闭环结果 | 系统显示完整的协作状态 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 无效状态提交

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至 loop 协作验证入口 | 系统显示协作配置界面 |
| 2 | 开发者在 loop 处于 completed 状态时尝试提交 | 系统检测无效状态 |
| 3 | 系统返回 LOOP_STATE_INVALID 错误 | 开发者看到错误详情和当前状态 |
| 4 | 开发者重置 loop 状态为 active | 系统接受状态变更 |
| 5 | 开发者重新提交 | 系统校验通过并进入主旅程步骤 3 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 回流边界违规

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者已收到 gate revise decision | 系统显示 decision 详情 |
| 2 | 开发者尝试回流到处于 completed 状态的 execution loop | 系统检测回流不允许 |
| 3 | 系统返回 REENTRY_NOT_ALLOWED 错误 | 开发者看到错误和目标 loop 状态 |
| 4 | 开发者修正 loop 状态或选择允许重入的目标 | 系统接受修正 |
| 5 | 开发者重新发起回流 | 系统校验通过 |

#### JOURNEY-RETRY-001: 重试旅程 — 下游规则违规

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 下游 workflow 注册了平行 handoff 规则 | 系统检测到违规 |
| 2 | 系统返回 PARALLEL_RULE_VIOLATION 错误 | 开发者看到违规规则和冲突详情 |
| 3 | 开发者移除平行规则，改为继承模式 | 系统接受规则修正 |
| 4 | 开发者重新触发继承验证 | 系统验证通过 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次协作验证流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
