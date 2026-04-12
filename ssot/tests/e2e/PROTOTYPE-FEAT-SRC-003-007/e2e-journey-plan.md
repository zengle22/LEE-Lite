# E2E Journey Plan — FEAT-SRC-003-007 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-007 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-007__runner-运行监控流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-007 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Operator 查看监控面 -> 系统展示 ready backlog, running, failed, deadletters, waiting-human 全状态 -> 数据关联到 job/invocation/outcome |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 监控面读取非 authoritative runner state（如目录扫描）-> 系统返回警告 -> 建议使用权威状态源 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P1 | 监控面尝试改写 runner control state -> 系统拒绝 -> 监控面只读 |
| 4 | JOURNEY-EXCEPTION-003 | exception | P1 | 观测结果无法关联到 job/invocation -> 返回关联断裂警告 |
| 5 | JOURNEY-RETRY-001 | retry | P1 | Operator 基于监控面决定 retry -> 触发重试 -> 监控面更新状态 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 全状态监控

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 执行 `ll loop monitor` | 系统初始化监控面 |
| 2 | 系统读取 authoritative runner state | 获取所有状态数据 |
| 3 | 系统展示 ready backlog 数量 | 显示待取件 job 列表 |
| 4 | 系统展示 running jobs 及 ownership | 显示运行中 job |
| 5 | 系统展示 failed jobs 及 failure reason | 显示失败 job |
| 6 | 系统展示 deadletters | 显示死信队列 |
| 7 | 系统展示 waiting-human jobs | 显示等待人工介入的 job |
| 8 | Operator 选择某个 job 查看详细信息 | 显示 lineage 关联（job -> invocation -> outcome） |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 非权威数据源

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 配置监控面使用目录扫描而非 authoritative state | 系统检测非权威数据源 |
| 2 | 系统返回 NON_AUTHORITATIVE_SOURCE 警告 | 建议使用权威 runner state |
| 3 | 监控数据标记为 unreliable | 数据带有警告标记 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 监控面尝试改写状态

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 监控面尝试直接修改 runner control state | 系统检测到越权操作 |
| 2 | 系统返回 MONITOR_WRITE_DENIED 错误 | 错误说明监控面只负责观察 |
| 3 | runner control state 不被修改 | 状态保持不变 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — 关联断裂

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 选择 job 查看详细 lineage | 系统尝试关联 invocation 和 outcome |
| 2 | 关联链断裂（如 outcome 文件被删除） | 系统返回 BROKEN_LINEAGE 警告 |
| 3 | 显示部分可用关联信息 | 显示 job 和 invocation，outcome 标记为 missing |

#### JOURNEY-RETRY-001: 重试旅程 — 基于监控面决定重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 查看监控面发现 failed jobs | 系统列出 failed job |
| 2 | Operator 决定重试某个 failed job | 触发 retry 操作 |
| 3 | 系统执行重试 | job 状态变为 running |
| 4 | Operator 查看监控面确认状态更新 | 监控面显示 job 不再在 failed 列表中 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 监控面为持续状态，回访已覆盖 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
