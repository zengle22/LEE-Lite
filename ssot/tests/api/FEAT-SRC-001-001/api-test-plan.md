# API Test Plan — FEAT-SRC-001-001

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-001-001 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-001-001__mainline-collaboration-loop.md`
- Acceptance Checks: 3 条 (AC-01 协作责任必须明确, AC-02 回流条件必须有边界, AC-03 下游不得重造协作规则)

## Capabilities Extracted from FEAT

从 FEAT-SRC-001-001 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| execution_loop | submit_object, define_reflow_state |
| gate_human_interface | consume_proposal, return_decision, trigger_progression |
| loop_responsibility | assign_transition_owner, verify_no_overlap |
| downstream_inheritance | inherit_collaboration_rules, detect_parallel_rule_violation |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | LOOP-EXEC-SUBMIT-001 | 执行循环提交 | 定义 execution loop 应提交什么对象、在何时进入 gate loop，以及哪些状态允许回流到 revision/retry | P0 |
| 2 | LOOP-GH-HANDOFF-001 | Gate-Human 交接界面 | 定义 gate loop 与 human loop 的衔接界面，包括谁消费 proposal、谁返回 decision、谁触发后续推进 | P0 |
| 3 | LOOP-RESPONSIBILITY-001 | Loop 责任分离 | 明确 loop 协作只覆盖推进责任、交接界面与回流条件，验证哪类对象触发 gate、哪类 decision 允许回流 | P0 |
| 4 | LOOP-REFLOW-BOUNDS-001 | 回流边界控制 | 明确返回什么对象、由谁消费、在什么 loop 状态下允许重入 | P0 |
| 5 | LOOP-INHERITANCE-001 | 下游协作规则继承 | 确保下游继承本 FEAT 的协作规则，而不是再发明并行 handoff/queue 模型 | P1 |

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
| LOOP-EXEC-SUBMIT-001 | 边界值 | 试点阶段对象提交为离散类型，无连续数值边界 | ADR-047 Section 4.1.3 |
| LOOP-GH-HANDOFF-001 | 边界值 | 交接界面为离散操作，无边界值概念 | ADR-047 Section 4.1.3 |
| LOOP-RESPONSIBILITY-001 | 参数校验 | 验证规则类能力，非 I/O 类能力 | ADR-047 Section 4.1.3 |
| LOOP-REFLOW-BOUNDS-001 | 边界值 | 回流条件为离散状态判断，无连续边界 | ADR-047 Section 4.1.3 |
| LOOP-INHERITANCE-001 | 边界值 | 继承验证为离散规则检查，无边界概念 | ADR-047 Section 4.1.3 |
| LOOP-INHERITANCE-001 | 状态约束 | P1 能力，状态约束裁剪 | ADR-047 Section 4.1.3 |
| LOOP-INHERITANCE-001 | 权限与身份 | 试点阶段无鉴权层 | ADR-047 Section 4.1.3 |
| LOOP-INHERITANCE-001 | 幂等/重试/并发 | P1 能力，并发场景裁剪 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | LOOP-EXEC-SUBMIT-001, LOOP-GH-HANDOFF-001, LOOP-RESPONSIBILITY-001, LOOP-REFLOW-BOUNDS-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | LOOP-INHERITANCE-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
