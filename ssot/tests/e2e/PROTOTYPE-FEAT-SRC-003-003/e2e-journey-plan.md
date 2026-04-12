# E2E Journey Plan — FEAT-SRC-003-003 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-003 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-003__runner-控制面流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-003 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Operator 执行完整控制面生命周期: start -> claim -> run -> complete -> 验证结构化输出 |
| 2 | JOURNEY-MAIN-002 | main | P0 | Operator 执行失败路径: start -> claim -> run -> fail -> 验证失败记录 |
| 3 | JOURNEY-EXCEPTION-001 | exception | P0 | Operator 尝试 run 未 claim 的 job -> 系统返回状态错误 |
| 4 | JOURNEY-EXCEPTION-002 | exception | P0 | Operator 尝试 claim 已 claim 的 job -> 系统返回已占用错误 |
| 5 | JOURNEY-EXCEPTION-003 | exception | P1 | Operator 使用分散的无治理脚本替代统一 CLI -> 系统拒绝或输出不合规 |
| 6 | JOURNEY-RETRY-001 | retry | P1 | Operator 执行 run 命令后 runner 超时 -> 重试 run 命令 -> 恢复执行 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 完整生命周期 (Happy Path)

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution` | 系统启动 runner，输出结构化启动状态 |
| 2 | Operator 执行 `ll job claim --job-id job-ready-001` | 系统输出 claim 确认和 ownership 信息 |
| 3 | Operator 执行 `ll job run --job-id job-ready-001` | 系统执行 job，输出执行进度 |
| 4 | 系统完成 job 执行 | 返回 execution result |
| 5 | Operator 执行 `ll job complete --job-id job-ready-001` | 系统输出完成确认和结构化状态 |
| 6 | Operator 验证输出为结构化格式 | JSON 格式的执行状态 |

#### JOURNEY-MAIN-002: 主旅程 — 失败生命周期

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop run-execution` | 系统启动 runner |
| 2 | Operator 执行 `ll job claim --job-id job-ready-002` | 系统输出 claim 确认 |
| 3 | Operator 执行 `ll job run --job-id job-ready-002` | job 执行失败 |
| 4 | Operator 执行 `ll job fail --job-id job-ready-002 --reason "skill_timeout"` | 系统输出失败确认和失败原因 |
| 5 | Operator 验证失败记录已持久化 | 失败状态文件存在 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 运行未 Claim 的 Job

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll job run --job-id job-ready-003` 但未先 claim | 系统返回 JOB_NOT_CLAIMED 错误 |
| 2 | 系统不执行 job | 无执行副作用 |
| 3 | 用户看到需先 claim 的提示 | 错误信息说明正确流程 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 重复 Claim

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 已成功 claim job-ready-004 | 系统记录 owner |
| 2 | Operator 再次执行 `ll job claim --job-id job-ready-004` | 系统返回 ALREADY_CLAIMED 错误 |
| 3 | 不创建新的 ownership 记录 | 原有 owner 不变 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — 分散脚本替代

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 外部脚本尝试替代 `ll job claim` 功能 | 系统不接受非统一控制面输入 |
| 2 | 控制面不认可外部操作 | job 状态不更新 |
| 3 | 审计日志中无有效 command evidence | 无追踪记录 |

#### JOURNEY-RETRY-001: 重试旅程 — Run 超时后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll job run --job-id job-ready-005` | 执行超时或挂起 |
| 2 | Operator 取消/中断命令 | 系统标记为 interrupted |
| 3 | Operator 重试 `ll job run --job-id job-ready-005` | 系统恢复或重新开始执行 |
| 4 | Job 完成 | 输出结构化完成状态 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 控制面命令为一次性操作，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001, JOURNEY-MAIN-002 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
