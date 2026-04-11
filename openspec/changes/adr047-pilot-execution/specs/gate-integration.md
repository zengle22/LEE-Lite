# Spec: Gate Integration

## Requirement: Gate Evaluator

系统必须能够:
- 读取 API manifest + E2E manifest
- 读取 waiver 记录
- 计算通过率 (排除 obsolete 和 approved waiver)
- 验证 waiver_status=pending 仍计入 failed
- 验证 lifecycle_status vs evidence_status 一致性

**验收标准**:
- lifecycle_status=passed 但 evidence_status!=complete 时 gate 拒绝
- waiver_status=pending 的 items 仍计入 failed/blocked/uncovered
- waiver_status=approved 的 items 从分母排除
- obsolete=true 的 items 从所有统计排除
- 分母计算正确: effective_denominator = total - approved_waivers

## Requirement: Release Gate Input 生成

系统必须能够:
- 生成机器可读的 `release_gate_input.yaml`
- 包含 API 链状态汇总 (status, uncovered_count, failed_count, blocked_count, waiver_refs)
- 包含 E2E 链状态汇总
- 包含执行日志哈希 (evidence_hash)
- 包含 gate 评估结果 (pass/fail/conditional_pass + 原因)

**验收标准**:
- YAML 格式可被标准解析器消费
- 所有必需字段存在且类型正确
- evidence_hash 为 SHA-256 截断字符串 (16 hex chars)
- final_decision 为 "release" | "conditional_release" | "block"

## Requirement: CI 消费验证

系统必须能够:
- 消费 release_gate_input.yaml
- 解析 YAML 并验证格式
- 根据 final_decision 执行 pass/fail 决策
- 记录消费结果

**验收标准**:
- YAML 可被 yaml.safe_load 解析
- 包含 api、e2e、final_decision 字段
- exit code: 0 (pass/conditional_release), 1 (block)
- 输出包含详细的链状态和决策原因

## Requirement: 防偷懒机制验证

系统必须验证以下约束:

| 约束 | 验证方式 |
|------|----------|
| Manifest items 执行前已冻结 | item count > 0 且 lifecycle_status 有非 designed 项时才允许执行 |
| 所有 cut 有 cut_record with approver | 审计所有 cut 状态 items 的 cut_record 完整性 |
| waiver_status=pending 计入 failed | 统计逻辑中不将 pending 排除出分母 |
| lifecycle_status=passed 但 evidence_status=missing 时 gate 拒绝 | 一致性检查 |
| 最小异常旅程覆盖 | E2E 至少 1 条 exception journey |
| 无 evidence 的 case 不算 executed | evidence_status=missing 时 lifecycle_status 不能为 passed |
| 执行日志哈希绑定 | evidence_hash 非空 |

**验收标准**:
- 7 项验证全部输出 PASS/FAIL 状态
- 任何 FAIL 项必须在 gate 决策中反映
