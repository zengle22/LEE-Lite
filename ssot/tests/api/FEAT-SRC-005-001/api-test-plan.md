# API Test Plan — FEAT-SRC-005-001

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-005-001 |
| plan_version | v1.0 |
| created_at | 2026-04-10 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-005-001__主链候选提交与交接流.md`
- Acceptance Checks: 3 条 (Loop responsibility, Submission completion, Downstream flow inheritance)

## Capabilities Extracted from FEAT

从 FEAT-SRC-005-001 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| candidate_package | submit, validate, create_handoff |
| handoff | create, read, transition_to_gate |
| gate_decision | evaluate, record_decision |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | CAND-SUBMIT-001 | 提交候选包 | 将 candidate package + proposal + evidence 提交为 authoritative handoff | P0 |
| 2 | CAND-VALIDATE-001 | 校验候选包 | 验证 candidate package 的完整性和格式合规性 | P0 |
| 3 | HANDOFF-CREATE-001 | 创建交接对象 | 生成 authoritative handoff object 并标记 pending-intake | P0 |
| 4 | HANDOFF-READ-001 | 读取交接对象 | 下游消费者读取 handoff 对象内容 | P1 |
| 5 | HANDOFF-TRANSITION-001 | 交接流转 | 将 handoff 对象推入 gate 消费链 | P0 |
| 6 | GATE-EVAL-001 | Gate 评估 | gate 读取 handoff 并生成 decision | P0 |
| 7 | GATE-RECORD-001 | 记录决策 | 持久化 gate decision 并暴露给下游 | P1 |
| 8 | LOOP-RESPONSIBILITY-001 | Loop 责任分离 | 验证哪类对象触发 gate、哪类 decision 回流、哪类状态推进 | P0 |

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
| HANDOFF-READ-001 | 幂等/重试/并发 | 纯读操作，无并发冲突场景 | ADR-047 Section 4.1.3 |
| GATE-RECORD-001 | 边界值 | 决策记录为离散值，无边界概念 | ADR-047 Section 4.1.3 |
| LOOP-RESPONSIBILITY-001 | 参数校验 | 验证规则类，非 I/O 类能力 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | CAND-SUBMIT-001, CAND-VALIDATE-001, HANDOFF-CREATE-001, HANDOFF-TRANSITION-001, GATE-EVAL-001, LOOP-RESPONSIBILITY-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | HANDOFF-READ-001, GATE-RECORD-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
