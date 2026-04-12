# E2E Journey Plan — FEAT-SRC-003-002 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-002 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-002__runner-用户入口流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-002 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Operator 通过 CLI 启动 runner -> 系统验证 skill bundle 存在 -> 绑定 ready queue -> 启动成功 |
| 2 | JOURNEY-MAIN-002 | main | P0 | Operator 通过 CLI 恢复之前中断的 runner -> 系统加载保存的 context -> 恢复成功 |
| 3 | JOURNEY-EXCEPTION-001 | exception | P0 | Operator 尝试启动但 skill bundle 不存在 -> 系统返回错误 |
| 4 | JOURNEY-EXCEPTION-002 | exception | P0 | Operator 尝试恢复但不存在之前会话 -> 系统返回无会话可恢复错误 |
| 5 | JOURNEY-EXCEPTION-003 | exception | P1 | Operator 尝试通过隐式后台方式触发 runner -> 系统拒绝非显式调用 |
| 6 | JOURNEY-RETRY-001 | retry | P1 | Operator 启动 runner 但 ready queue 不可达 -> 修复后重试 -> 启动成功 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 启动 Runner

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution --start` | 系统验证 skill bundle 存在 |
| 2 | 系统绑定 ready queue (artifacts/jobs/ready) | 用户看到 queue 绑定确认 |
| 3 | 系统启动 runner 并保留 run context | 用户看到 "Runner started" 确认 |
| 4 | Operator 验证 skill authority 已设置 | 系统显示 canonical bundle path |

#### JOURNEY-MAIN-002: 主旅程 — 恢复 Runner

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution --resume` | 系统查找之前保存的 session |
| 2 | 系统加载保存的 run context 和 lineage | 用户看到 context 加载确认 |
| 3 | 系统恢复 runner 到之前状态 | 用户看到 "Runner resumed" 确认 |
| 4 | Operator 验证 lineage 完整性 | lineage refs 匹配之前会话 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — Skill Bundle 不存在

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution --start` 但 skills/l3/ll-execution-loop-job-runner/ 不存在 | 系统返回 BUNDLE_NOT_FOUND 错误 |
| 2 | 系统不启动 runner | 无 runner 进程 |
| 3 | 用户看到明确的 bundle 路径和错误信息 | 错误信息指向正确安装方式 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 无可恢复会话

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution --resume` 但无保存的 session | 系统返回 NO_PRIOR_SESSION 错误 |
| 2 | 系统不启动 runner | 无 runner 进程 |
| 3 | 用户看到建议改用 --start 的提示 | 提示信息指导正确操作 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — 隐式后台调用被拒绝

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 外部脚本尝试绕过 CLI 直接调用 runner | 系统拒绝非显式调用 |
| 2 | 系统返回 UNAUTHORIZED_INVOCATION 错误 | 错误说明必须通过 skill adapter |
| 3 | runner 不启动 | 无副作用 |

#### JOURNEY-RETRY-001: 重试旅程 — Queue 不可达后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 启动 runner 但 artifacts/jobs/ready 不可达 | 系统返回 QUEUE_UNREACHABLE 错误 |
| 2 | Operator 修复目录权限/创建目录 | 目录就绪 |
| 3 | Operator 重试 `ll loop run-execution --start` | 系统启动成功 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次启动流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001, JOURNEY-MAIN-002 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
