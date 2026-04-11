---
description: "从 prototype 生成 E2E 旅程计划 (ADR-047 双链治理)"
---

# Skill: prototype-to-e2e-journey-plan

## Role

从冻结的 prototype 文档 (或从 feat 推导) 提取用户旅程, 生成 `e2e-journey-plan.md` 和 `e2e-coverage-manifest.yaml`。

## Input

- `prototype_path`: 路径到 prototype 文件 (可选, 如无则使用 API-derived 模式)
- `feat_path`: 路径到 feat markdown 文件 (API-derived 模式必需)
- `output_dir`: 输出目录 (默认为 `ssot/tests/e2e/{prototype_id}/`)

## Modes

### Mode A: Prototype-Driven

当存在真实 prototype 资产时:
- 从 prototype 的 flow map / journey map 提取旅程
- 识别页面入口、用户动作序列、页面反馈、页面跳转
- 按旅程类型分类 (main/branch/exception/revisit/state)

### Mode B: API-Derived

当无 prototype 资产时:
- 从 feat 的 Scope / Acceptance Checks 推导用户可见行为
- 将 API capabilities 映射为用户操作步骤
- 标注 `derivation_mode: api-derived`

## Journey Identification Rules

| 触发条件 | 必须识别的旅程 | 优先级 |
|----------|----------------|--------|
| 每个页面流 | 至少 1 条主旅程 | P0 |
| 每个表单页 | 至少 1 条校验失败异常旅程 | P0 |
| 每个有状态差异的页面 | 至少 1 条状态型旅程 | P1 |
| 每个有回访入口的闭环 | 至少 1 条 revisit 旅程 | P1 |
| 每个主旅程 | 至少 1 条关键分支旅程 | P1 |
| 每个网络请求点 | 至少 1 条网络失败异常旅程 | P1 |

## Output

- `e2e-journey-plan.md`
- `e2e-coverage-manifest.yaml`

## Manifest Schema

```yaml
e2e_coverage_manifest:
  prototype_id: {proto_id}
  derivation_mode: {prototype-driven|api-derived}
  generated_at: {timestamp}
  source_plan_ref: {plan_path}
  items:
    - coverage_id: {coverage_id}
      journey_id: {journey_id}
      journey_type: {main|exception|branch|retry|state}
      priority: {P0|P1}
      source_prototype_ref: {proto_ref}
      lifecycle_status: designed
      mapping_status: unmapped
      evidence_status: missing
      waiver_status: none
```

## Quality Checks

- [ ] 至少 1 条主旅程 (P0)
- [ ] 至少 1 条异常旅程
- [ ] manifest item count >= plan journeys
- [ ] 所有 cut 记录有 cut_record with approver + source_ref
