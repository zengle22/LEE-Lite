# E2E Journey Plan — FEAT-SRC-001-004 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-001-004 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-001-004__mainline-io-and-path-governance.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 开发者配置主链 IO 路径 -> 系统验证 IO 边界合规 -> 开发者执行正式写入 -> 系统确认写入遵守 path/mode 约束 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 开发者尝试将超范围 IO 纳入主链治理 -> 系统拒绝并返回超作用域错误 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 正式写入遇到 path/mode 限制后尝试 silent fallback -> 系统拒绝并强制执行 |
| 4 | JOURNEY-RETRY-001 | retry | P1 | 下游 skill 自定义路径规则 -> 系统检测违规 -> 开发者修正为继承模式后重新验证 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 主链 IO 与路径治理

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者导航至主链 IO 配置入口 | 系统显示 IO 路径配置界面 |
| 2 | 开发者配置手写入路径和目录边界 | 系统实时校验路径合规性 |
| 3 | 开发者提交 IO 配置 | 系统验证 IO 边界 |
| 4 | 开发者执行正式写入操作 | 系统确认写入遵守 path/mode 约束 |
| 5 | 开发者查看路径治理结果 | 系统显示完整的治理状态 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 超范围 IO

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 开发者尝试将仓库级文件治理规则纳入主链 | 系统检测超范围 IO |
| 2 | 系统返回 OUT_OF_SCOPE_IO 错误 | 开发者看到超出范围的路径详情 |
| 3 | 开发者移除超范围路径 | 系统接受修正 |
| 4 | 开发者重新提交 | 系统校验通过 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — Silent Fallback

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 正式写入遇到 path/mode 限制 | 系统返回写入受限错误 |
| 2 | 写入方尝试 silent fallback 到自由写入 | 系统检测并阻断 fallback |
| 3 | 系统返回 SILENT_FALLBACK_BLOCKED 错误 | 开发者看到强制执行确认 |

#### JOURNEY-RETRY-001: 重试旅程 — 自定义路径规则

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 下游 skill 自定义等价路径规则 | 系统检测自定义规则 |
| 2 | 系统返回 CUSTOM_PATH_RULE 错误 | 开发者看到冲突详情 |
| 3 | 开发者移除自定义规则，改为继承 | 系统接受修正 |
| 4 | 开发者重新验证 | 系统校验通过 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次 IO 验证流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
