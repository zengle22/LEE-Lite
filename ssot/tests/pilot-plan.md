# ADR-047 Pilot Plan

## Pilot Objective

验证 ADR-047 (v1.4, Trial Approved) 定义的"双链治理"测试架构在真实项目中的可行性。

## Pilot Scope

| 维度 | 值 |
|------|-----|
| **API 链锚点** | `FEAT-SRC-005-001` (主链候选提交与交接流) |
| **E2E 链锚点** | `PROTOTYPE-FEAT-SRC-005-001` (待确认/创建) |
| **试点范围** | 单 feat + prototype 对 |
| **验证目标** | plan -> manifest -> spec -> tests -> evidence -> settlement -> release_gate_input |

## Phase 1: 试点准备 — 候选评估

### FEAT-SRC-005-001 最小可测试性评估

| 要求 | 状态 | 说明 |
|------|------|------|
| capability 明确 | PASS | 定义了 candidate package 提交、authoritative handoff 创建、gate 消费链三个核心能力 |
| 输入输出明确 | PASS | 输入：candidate package + proposal + evidence；输出：authoritative handoff object |
| 关键业务规则明确 | PASS | 3 条 Acceptance Checks 定义了 loop responsibility split、submission completion visibility、downstream flow inheritance |
| 状态迁移明确 | PARTIAL | 涉及 candidate -> handoff -> gate 的状态流转，但具体状态机定义需从 feat 推导 |
| 成功/失败验收标准明确 | PASS | 3 条 Acceptance Checks 提供了明确的验收判定标准 |

**结论**: FEAT-SRC-005-001 满足最小可测试要求，可作为 API 链试点锚点。

### PROTOTYPE-FEAT-SRC-005-001 最小可测试性评估

| 要求 | 状态 | 说明 |
|------|------|------|
| 页面入口明确 | BLOCKED | 未找到对应的 prototype 资产 |
| 主旅程至少一条 | BLOCKED | 无 prototype 无法定义旅程 |
| 异常反馈定义 | BLOCKED | 无 prototype 无法定义 |
| 关键状态差异 | BLOCKED | 无 prototype 无法定义 |
| 关键页面反馈 | BLOCKED | 无 prototype 无法定义 |

**结论**: PROTOTYPE-FEAT-SRC-005-001 不存在。E2E 链试点需要调整策略。

### 调整策略

由于 `PROTOTYPE-FEAT-SRC-005-001` 不存在，E2E 链试点采用以下降级方案：

1. **E2E 链锚点**: 从 FEAT-SRC-005-001 的功能契约推导用户旅程（API-to-UI 推导模式）
2. **使用现有 prototype**: 参考 `ssot/prototype/SRC-003/PROTO-RUNNER-OPERATOR-MAIN/` 的结构模式
3. **创建最小 prototype 契约**: 在 e2e-journey-plan 中定义推导的用户旅程，标注来源为"API-derived"

### 备用候选

| 链 | 主候选 | 备用候选 |
|-----|--------|---------|
| API | FEAT-SRC-005-001 | FEAT-SRC-004-001 |
| E2E | PROTOTYPE-FEAT-SRC-005-001 (不存在) | PROTOTYPE-SRC-003 (存在但不对应) |

### 选择理由

选择 FEAT-SRC-005-001 作为 API 链试点：
- 边界清晰：candidate package -> handoff -> gate 的流程明确
- I/O 合约清楚：输入输出对象有明确定义
- 验收标准可量化：3 条 Acceptance Checks 可映射为测试维度
- 是主链 (SRC-005) 的核心能力，具有代表性

## Success Criteria

| 标准 | 验收方式 |
|------|----------|
| API 链完整走完 | plan -> manifest -> spec -> tests -> evidence -> settlement 全链路产出物 |
| E2E 链降级走完 | plan -> manifest -> spec (derived) -> 至少定义完整 |
| Gate evaluator 正确生成 | release_gate_input.yaml 格式正确，决策逻辑可验证 |
| 裁剪记录带审批链 | 所有 cut_record 包含 approver + source_ref |
| 分层状态字段正确 | lifecycle/mapping/evidence/waiver 四维状态正确追踪 |
| 防偷懒机制验证通过 | 7 项验证全部通过 |

## Risk Log

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| E2E 链无 prototype 锚点 | 高 | 采用 API-derived 模式，从 feat 推导用户旅程 |
| 实际后端服务不可用 | 高 | 使用 mock 数据执行 API 测试 |
| Gate evaluator 逻辑复杂 | 中 | 从简化版本开始，迭代完善 |
