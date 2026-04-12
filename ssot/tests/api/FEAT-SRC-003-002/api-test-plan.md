# API Test Plan — FEAT-SRC-003-002

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-002 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-002__runner-用户入口流.md`
- Acceptance Checks: 3 条 (Named skill entry, User-invokable entry, Explicit runner skill authority)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-002 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| skill_bundle | expose, validate_entry |
| runner_entry | start, resume, bind_queue |
| run_context | preserve_authority, maintain_lineage |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | BUNDLE-EXPOSE-001 | 暴露 Skill Bundle | 暴露独立 canonical governed skill bundle `skills/l3/ll-execution-loop-job-runner/` | P0 |
| 2 | ENTRY-START-001 | 启动 Runner 入口 | operator 通过 CLI 显式启动 execution loop runner | P0 |
| 3 | ENTRY-RESUME-001 | 恢复 Runner 入口 | operator 通过 CLI 显式恢复之前中断/暂停的 runner 会话 | P0 |
| 4 | QUEUE-BIND-001 | 绑定 Ready Queue | 入口声明与 ready queue 的绑定关系，确定取件源 | P0 |
| 5 | CONTEXT-PRESERVE-001 | 保留 Run Context | 入口调用保留 authoritative run context 与 lineage | P0 |
| 6 | SKILL-AUTH-001 | Skill Authority 校验 | 验证入口通过 skill adapter 调用而非隐式后台或手工接力 | P1 |

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
| SKILL-AUTH-001 | 边界值 | Skill 认证为存在性检查，无连续边界 | ADR-047 Section 4.1.3 |
| SKILL-AUTH-001 | 幂等/重试/并发 | 纯验证操作，无并发副作用 | ADR-047 Section 4.1.3 |
| QUEUE-BIND-001 | 边界值 | 队列绑定为离散引用，无数值边界 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | BUNDLE-EXPOSE-001, ENTRY-START-001, ENTRY-RESUME-001, QUEUE-BIND-001, CONTEXT-PRESERVE-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | SKILL-AUTH-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
