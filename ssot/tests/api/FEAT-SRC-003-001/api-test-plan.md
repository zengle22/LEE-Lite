# API Test Plan — FEAT-SRC-003-001

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-001 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-001__批准后-ready-job-生成流.md`
- Acceptance Checks: 3 条 (Approve emits governed dispatch, Approve not rewritten as formal publication, Non-approve decisions excluded)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-001 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| ready_job | generate, emit_with_refs, validate_progression |
| hold_job | route_to_hold, prevent_queue_leak |
| gate_decision | filter_non_approve, trace_approval |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | JOB-GEN-001 | 批准后生成 Job | 根据 gate approve 和 progression_mode 生成 ready execution job 或 hold job | P0 |
| 2 | JOB-EMIT-001 | 发射 Ready Job | 将 ready job 写入 `artifacts/jobs/ready`，包含 authoritative refs、next skill target | P0 |
| 3 | HOLD-ROUTE-001 | Hold Job 路由 | progression_mode=hold 时将 job 路由到 hold/waiting-human 队列，不泄漏到 ready queue | P0 |
| 4 | FILTER-APPROVE-001 | 过滤非 approve 决策 | 确保 revise/retry/reject/handoff 决策不会生成 next-skill ready job | P0 |
| 5 | PROG-VALIDATE-001 | 验证 Progression Mode | 校验 progression_mode 枚举值 (auto-continue | hold) 及其治理语义 | P0 |
| 6 | TRACE-JOB-001 | Job 溯源 | 保证 approve-to-job 关系可追溯，保留 lineage 记录 | P1 |

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
| HOLD-ROUTE-001 | 边界值 | hold 路由为离散状态转移，无连续边界 | ADR-047 Section 4.1.3 |
| FILTER-APPROVE-001 | 幂等/重试/并发 | 过滤器为纯判断逻辑，无并发副作用 | ADR-047 Section 4.1.3 |
| TRACE-JOB-001 | 边界值 | 溯源为元数据关联，无数值边界 | ADR-047 Section 4.1.3 |
| TRACE-JOB-001 | 状态约束 | 溯源记录为只读追加，无状态机 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | JOB-GEN-001, JOB-EMIT-001, HOLD-ROUTE-001, FILTER-APPROVE-001, PROG-VALIDATE-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | TRACE-JOB-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
