# API Test Plan — FEAT-SRC-003-003

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-003 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-003__runner-控制面流.md`
- Acceptance Checks: 3 条 (Explicit CLI controls, Structured control results, Unified control surface)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-003 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| cli_control | start, claim, run, complete, fail |
| runner_lifecycle | map_to_lifecycle, emit_structured_state |
| command_evidence | record_evidence, track_state |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | CTRL-START-001 | 启动控制命令 | `ll loop run-execution` 启动 runner 生命周期 | P0 |
| 2 | CTRL-CLAIM-001 | Claim 控制命令 | `ll job claim` 声明 job ownership | P0 |
| 3 | CTRL-RUN-001 | Run 控制命令 | `ll job run` 执行已 claim 的 job | P0 |
| 4 | CTRL-COMPLETE-001 | Complete 控制命令 | `ll job complete` 标记 job 完成 | P0 |
| 5 | CTRL-FAIL-001 | Fail 控制命令 | `ll job fail` 标记 job 失败并记录原因 | P0 |
| 6 | STATE-STRUCTURE-001 | 结构化状态输出 | 控制面输出结构化执行状态而非隐式日志 | P0 |
| 7 | CMD-TRACE-001 | 命令追踪 | 控制动作产生可追踪的 command/state evidence | P1 |

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
| CMD-TRACE-001 | 边界值 | 追踪为元数据记录，无连续边界 | ADR-047 Section 4.1.3 |
| STATE-STRUCTURE-001 | 幂等/重试/并发 | 结构化输出为格式化验证，无并发场景 | ADR-047 Section 4.1.3 |
| CTRL-COMPLETE-001 | 幂等/并发 | 完成操作为终态标记，并发测试延后 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | CTRL-START-001, CTRL-CLAIM-001, CTRL-RUN-001, CTRL-COMPLETE-001, CTRL-FAIL-001, STATE-STRUCTURE-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | CMD-TRACE-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
