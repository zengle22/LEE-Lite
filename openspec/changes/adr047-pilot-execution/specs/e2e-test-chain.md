# Spec: E2E Test Chain

## Requirement: E2E 旅程计划生成

系统必须能够:
- 从 prototype 或从 feat 推导用户旅程
- 生成包含旅程定义的 `e2e-journey-plan.md`
- 应用旅程识别规则 (主旅程 + 最小异常旅程枚举)

**验收标准**:
- 至少 1 条主旅程 (P0)
- 至少 1 条异常旅程
- 每条旅程有 journey_id、type、priority
- 裁剪记录包含 cut_target、cut_reason、source_ref、approver、approved_at

## Requirement: E2E 覆盖清单管理

系统必须能够:
- 为每个 journey 创建 coverage item
- 追踪四维状态: lifecycle_status、mapping_status、evidence_status、waiver_status
- 验证 item count >= plan journeys

**验收标准**:
- 每个 item 有 coverage_id、journey_id、journey_type、priority
- 异常旅程覆盖率 >= 1 (全局最少 1 条)
- 所有 cut 项有 cut_record

## Requirement: E2E 旅程规格定义

系统必须能够:
- 为每个 journey 创建结构化测试合同
- 定义 entry_point、user_steps、expected_ui_states
- 定义 anti_false_pass_checks 和 evidence_required

**验收标准**:
- 每个 spec 有 case_id、coverage_id、journey_id、entry_point
- 每个 spec 包含 user_steps 列表
- 每个 spec 包含 expected_ui_states、expected_network_events
- 每个 spec 包含 expected_persistence 和 anti_false_pass_checks
- 每个 spec 的 evidence_required 包含 playwright_trace + network_log

## Requirement: E2E 测试结算报告

系统必须能够:
- 统计总 journey 数和按旅程类型分类
- 统计 main/branch/exception/revisit 旅程数
- 按 prototype ref 分类覆盖状态

**验收标准**:
- 报告包含异常旅程覆盖率
- 报告包含 gap list 和 waiver list
- 报告包含按 journey 类型分布的覆盖状态
