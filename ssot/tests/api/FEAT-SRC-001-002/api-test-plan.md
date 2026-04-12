# API Test Plan — FEAT-SRC-001-002

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-001-002 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-001-002__formal-handoff-and-materialization.md`
- Acceptance Checks: 3 条 (AC-01 正式升级路径必须唯一, AC-02 candidate 不得绕过 gate, AC-03 formalization 不得回流进业务 skill)

## Capabilities Extracted from FEAT

从 FEAT-SRC-001-002 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| handoff | upgrade_to_formal, verify_single_path |
| gate_decision | enforce_gate_only_upgrade, block_bypass |
| formal_materialization | create_formal, prevent_skill_reflow |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | HANDOFF-UPGRADE-001 | 正式升级路径 | 定义 handoff -> gate decision -> formal materialization 的单一路径推进规则 | P0 |
| 2 | CANDIDATE-GATE-ENFORCE-001 | Gate 旁路阻断 | 确保 candidate 只能作为 gate 消费对象，不得绕过 gate 直接成为 downstream formal input | P0 |
| 3 | FORMAL-NO-REFLOW-001 | Formalization 防回流 | 确保 formalization decision 与 materialization action 保持在业务 skill 之外 | P0 |
| 4 | DECISION-SEMANTICS-001 | 统一 Decision 语义 | 要求下游继承同一套 approve/revise/retry/handoff/reject 语义，不得并列批准语义 | P1 |

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
| HANDOFF-UPGRADE-001 | 边界值 | 升级路径为离散状态转换，无连续数值边界 | ADR-047 Section 4.1.3 |
| CANDIDATE-GATE-ENFORCE-001 | 边界值 | 旁路阻断为二元判定，无边界概念 | ADR-047 Section 4.1.3 |
| FORMAL-NO-REFLOW-001 | 边界值 | 回流防护为离散规则，无边界概念 | ADR-047 Section 4.1.3 |
| DECISION-SEMANTICS-001 | 状态约束 | P1 能力，状态约束裁剪 | ADR-047 Section 4.1.3 |
| DECISION-SEMANTICS-001 | 权限与身份 | 试点阶段无鉴权层 | ADR-047 Section 4.1.3 |
| DECISION-SEMANTICS-001 | 幂等/重试/并发 | P1 能力，并发场景裁剪 | ADR-047 Section 4.1.3 |
| DECISION-SEMANTICS-001 | 边界值 | 语义验证为离散规则检查 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | HANDOFF-UPGRADE-001, CANDIDATE-GATE-ENFORCE-001, FORMAL-NO-REFLOW-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | DECISION-SEMANTICS-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
