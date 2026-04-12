# E2E Journey Plan — FEAT-SRC-001-003 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-001-003 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-001-003__object-layering-and-admission.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 开发者配置对象分层 -> 系统验证 candidate 与 formal 分离 -> 开发者设置 consumer 准入基于 formal refs -> 系统验证无业务 skill gate 权限 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 开发者尝试混层 candidate 与 formal 对象 -> 系统拒绝并返回分层违规错误 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 开发者尝试通过 path guessing 读取对象 -> 系统拒绝并返回准入错误 |
| 4 | JOURNEY-RETRY-001 | retry | P1 | 业务 skill 静默继承 gate 权限 -> 系统检测并拒绝 -> 开发者修正权限边界后重新验证 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 对象分层与准入

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至对象分层验证入口 | 系统显示分层配置界面 |
| 2 | 开发者配置 candidate 和 formal layer 对象 | 系统实时校验分层合规性 |
| 3 | 开发者提交分层配置 | 系统验证 layer separation |
| 4 | 开发者配置 consumer 基于 formal refs 的准入规则 | 系统验证准入规则合规 |
| 5 | 开发者查看分层验证结果 | 系统显示完整的分层状态 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 分层混层

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者将同一对象同时标记为 candidate 和 formal | 系统检测混层企图 |
| 2 | 系统返回 LAYER_MIXING 错误 | 开发者看到混层对象详情 |
| 3 | 开发者修正对象分层 | 系统接受修正 |
| 4 | 开发者重新提交 | 系统校验通过 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — Path Guessing 准入

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者尝试通过相邻文件发现读取 formal 对象 | 系统检测 path guessing |
| 2 | 系统返回 PATH_GUESSING_BLOCKED 错误 | 开发者看到错误和正确的 formal refs 准入方式 |
| 3 | 开发者改用 formal refs 方式访问 | 系统校验通过 |

#### JOURNEY-RETRY-001: 重试旅程 — 静默 gate 权限

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 业务 skill 产出 candidate 并尝试充当 gate approver | 系统检测静默继承 |
| 2 | 系统返回 SILENT_GATE_INHERITANCE 错误 | 开发者看到权限冲突详情 |
| 3 | 开发者将 gate 权限从业务 skill 剥离 | 系统接受修正 |
| 4 | 开发者重新验证 | 系统校验通过 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次分层验证流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
