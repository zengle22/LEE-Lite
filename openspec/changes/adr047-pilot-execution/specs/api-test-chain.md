# Spec: API Test Chain

## Requirement: API 测试计划生成

系统必须能够:
- 从冻结的 feat 文档提取 capabilities
- 生成包含范围定义和优先级矩阵的 `api-test-plan.md`
- 每个 capability 必须有明确的 capability_id、name、description、priority

**验收标准**:
- api-test-plan.md 包含 feature_id、source_feat_refs、api_objects、priorities
- P0 capabilities 必须有至少 5 个测试维度覆盖
- 任何裁剪必须有 cut_record (含 cut_reason、source_ref、approver、approved_at)

## Requirement: API 覆盖清单管理

系统必须能够:
- 为每个 capability × dimension 创建 coverage item
- 追踪四维状态: lifecycle_status、mapping_status、evidence_status、waiver_status
- 所有 items 初始化时 lifecycle_status=designed

**验收标准**:
- coverage item count = capabilities × required dimensions (排除已裁剪项)
- 每个 item 有 coverage_id、capability、scenario_type、dimension、priority
- 裁剪项必须包含 cut_record 字段
- obsolete items 不得计入统计分母

## Requirement: API 测试规格定义

系统必须能够:
- 为每个 coverage item 创建结构化测试合同
- 定义 preconditions、request、expected response、assertions
- 定义 evidence_required 字段

**验收标准**:
- 每个 spec 有 case_id、coverage_id、endpoint、capability
- 每个 spec 包含 expected.response_assertions 和 side_effect_assertions
- 每个 spec 包含 evidence_required 列表
- 每个 spec 包含 cleanup 步骤

## Requirement: API 测试结算报告

系统必须能够:
- 统计 total/designed/executed/passed/failed/blocked/uncovered 数量
- 按 capability 和 feat ref 分类覆盖状态
- 列出 gap list 和 waiver list

**验收标准**:
- 报告包含所有统计指标
- gap list 列出所有未覆盖项
- waiver list 列出所有审批豁免
