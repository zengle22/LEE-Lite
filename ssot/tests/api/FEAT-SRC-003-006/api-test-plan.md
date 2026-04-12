# API Test Plan — FEAT-SRC-003-006

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-006 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-006__执行结果回写与重试边界流.md`
- Acceptance Checks: 3 条 (Explicit outcomes, Retry returns to execution, Approve not terminal)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-006 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| execution_outcome | record_done, record_failed, record_retry_reentry |
| failure_evidence | bind_evidence_to_attempt, store_failure_reason |
| retry_directive | create_reentry_directive, route_to_execution |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | OUTCOME-DONE-001 | 记录 Done 结果 | 显式记录 execution done 结果及证据 | P0 |
| 2 | OUTCOME-FAIL-001 | 记录 Failed 结果 | 显式记录 execution failed 结果、failure reason 和证据 | P0 |
| 3 | OUTCOME-RETRY-001 | 记录 Retry/Reentry 结果 | 显式记录 retry-reentry directive，回到 execution semantics | P0 |
| 4 | FAILURE-BIND-001 | 失败证据绑定 | 将失败证据与 execution attempt 严格绑定 | P0 |
| 5 | STATE-TRANSITION-001 | 状态转移 (running -> done/failed/retry) | 定义 running 到终态/回流态的合法状态边界 | P0 |
| 6 | CHAIN-CONTINUE-001 | 链路持续性验证 | 验证 approve 不是终态，链路通过 runner 继续推进 | P1 |

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
| CHAIN-CONTINUE-001 | 边界值 | 链路持续性为验证规则，无连续边界 | ADR-047 Section 4.1.3 |
| CHAIN-CONTINUE-001 | 状态约束 | 验证规则类能力，无独立状态机 | ADR-047 Section 4.1.3 |
| OUTCOME-RETRY-001 | 边界值 | Retry directive 为离散枚举，无边界概念 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | OUTCOME-DONE-001, OUTCOME-FAIL-001, OUTCOME-RETRY-001, FAILURE-BIND-001, STATE-TRANSITION-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | CHAIN-CONTINUE-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
