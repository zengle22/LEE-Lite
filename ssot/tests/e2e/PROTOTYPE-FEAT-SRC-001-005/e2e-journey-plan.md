# E2E Journey Plan — FEAT-SRC-001-005 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-001-005 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-001-005__governed-skill-adoption-and-cross-skill-e2e.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 开发者注册 governed skill -> 系统验证 onboarding 矩阵 -> 开发者执行迁移波次 -> 开发者运行跨 skill E2E pilot 链 -> 系统生成 E2E evidence |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 开发者尝试 onboard 未定义 skill 类型 -> 系统拒绝并返回无效 skill 错误 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 开发者尝试一次性全量迁移所有 skill -> 系统拒绝并强制分批迁移 |
| 4 | JOURNEY-RETRY-001 | retry | P1 | 开发者尝试将 adoption 扩展为仓库级治理 -> 系统拒绝并限制范围 -> 开发者修正 scope 后重新验证 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 技能接入与跨 skill E2E 闭环

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至技能接入验证入口 | 系统显示 onboarding 配置界面 |
| 2 | 开发者注册 governed skill 并配置接入矩阵 | 系统实时校验 onboarding 参数 |
| 3 | 开发者提交 onboarding 配置 | 系统验证接入矩阵完整性 |
| 4 | 开发者配置迁移波次和 cutover/fallback 规则 | 系统验证迁移规则合规 |
| 5 | 开发者执行 producer -> consumer -> audit -> gate pilot 链 | 系统执行并生成 E2E evidence |
| 6 | 开发者查看 E2E 证据报告 | 系统显示完整的闭环验证结果 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 无效 Skill 类型

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者尝试注册未定义的 skill 类型 | 系统检测无效 skill |
| 2 | 系统返回 INVALID_SKILL_TYPE 错误 | 开发者看到无效类型详情和允许的枚举值 |
| 3 | 开发者修正 skill 类型 | 系统接受修正 |
| 4 | 开发者重新提交 | 系统校验通过 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 全量迁移拒绝

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者配置一次性全量迁移所有 governed skill | 系统检测全量迁移企图 |
| 2 | 系统返回 FULL_MIGRATION_BLOCKED 错误 | 开发者看到错误和分批迁移要求 |
| 3 | 开发者改为配置分波次迁移 | 系统接受修正 |
| 4 | 开发者重新提交 | 系统校验通过 |

#### JOURNEY-RETRY-001: 重试旅程 — 作用域膨胀

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者尝试将 adoption 范围扩展到仓库级文件治理 | 系统检测作用域膨胀 |
| 2 | 系统返回 SCOPE_EXPANSION_BLOCKED 错误 | 开发者看到超范围内容 |
| 3 | 开发者修正为本主链 governed skills 范围 | 系统接受修正 |
| 4 | 开发者重新验证 | 系统校验通过 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次接入验证流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
