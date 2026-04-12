# API Test Plan — FEAT-SRC-003-007

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-007 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-007__runner-运行监控流.md`
- Acceptance Checks: 3 条 (Core queue states visible, Monitoring supports operator action, Observability covers critical states)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-007 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| monitor_surface | list_ready_backlog, list_running, list_failed, list_deadletters, list_waiting_human |
| operator_decision | suggest_resume, suggest_retry, suggest_handoff |
| lineage_correlation | correlate_job_to_invocation, correlate_to_outcome |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | MON-BACKLOG-001 | 查看 Ready Backlog | 列出 ready queue 中等待取件的 job 集合 | P0 |
| 2 | MON-RUNNING-001 | 查看 Running Jobs | 列出当前 running 状态的 job 集合及其 ownership | P0 |
| 3 | MON-FAILED-001 | 查看 Failed Jobs | 列出 failed 状态的 job 集合及 failure reason | P0 |
| 4 | MON-DEADLETTER-001 | 查看 Deadletters | 列出 deadletter 队列中的 job 集合 | P0 |
| 5 | MON-WAITING-001 | 查看 Waiting-Human Jobs | 列出 waiting-human 状态的 job 集合 | P0 |
| 6 | MON-CORRELATE-001 | 关联 Lineage | 将观测结果关联到 ready job、invocation 和 execution outcome | P0 |
| 7 | OPERATOR-ACTION-001 | 操作建议 | 基于监控面输出 resume/retry/handoff 操作建议 | P1 |

## Test Dimension Matrix

每个 capability 按以下维度评估覆盖范围：

| 维度 | 说明 |
|------|------|
| **正常路径** | 合法输入、正确响应、正确副作用 |
| **参数校验** | 必填缺失、类型错误、格式错误、非法枚举、越界值 |
| **边界值** | 最小值/最大值、空集合/空字符串 |
| **状态约束** | 合法状态迁移、非法状态迁移、重复提交 |
| **权限与身份** | 未授权访问、无权限操作 |
| **异常路径** | 资源不存在、冲突、上游依赖失败、业务拒绝 |
| **幂等/重试/并发** | 重复请求、并发提交 |
| **数据副作用** | DB 正确写入、关联对象同步变化 |

## Coverage Cut Records

| Capability | Dimension | Cut Reason | Source Ref |
|------------|-----------|------------|------------|
| MON-BACKLOG-001 | 边界值 | 空 backlog 为正常状态，无需额外边界测试 | ADR-047 Section 4.1.3 |
| OPERATOR-ACTION-001 | 边界值 | 操作建议为离散枚举，无连续边界 | ADR-047 Section 4.1.3 |
| OPERATOR-ACTION-001 | 权限与身份 | 试点阶段无鉴权层，无法模拟不同角色 | ADR-047 Section 4.1.3 |
| OPERATOR-ACTION-001 | 幂等/重试/并发 | 建议生成为只读操作，无并发副作用 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | MON-BACKLOG-001, MON-RUNNING-001, MON-FAILED-001, MON-DEADLETTER-001, MON-WAITING-001, MON-CORRELATE-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key) |
| P1 | OPERATOR-ACTION-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
