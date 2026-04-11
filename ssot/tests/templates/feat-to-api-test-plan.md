---
description: "从 feat 生成 API 测试计划 (ADR-047 双链治理)"
---

# Skill: feat-to-api-test-plan

## Role

从冻结的 feat 文档提取 capabilities, 生成 `api-test-plan.md` 和 `api-coverage-manifest.yaml`。

## Input

- `feat_path`: 路径到 feat markdown 文件
- `output_dir`: 输出目录 (默认为 `ssot/tests/api/{feat_id}/`)

## Workflow

### Step 1: Parse Feat

- 读取 feat frontmatter 获取 id, title, status
- 提取 Scope 部分识别 capabilities
- 提取 Acceptance Checks 识别验收标准
- 提取 Constraints 识别边界约束

### Step 2: Identify Capabilities

对每个 capability 识别:
- capability_id (格式: `{prefix}-{capability}-{seq}`)
- name (简短描述)
- description (详细行为定义)
- priority (P0/P1/P2)

### Step 3: Apply Dimension Matrix

为每个 capability 应用测试维度:
- 正常路径
- 参数校验 (P0/P1 必测)
- 边界值 (P0 选测, P1/P2 裁剪)
- 状态约束 (P0 必测)
- 权限与身份 (P0 必测)
- 异常路径 (P0/P1 必测)
- 幂等/重试/并发 (P0 选测)
- 数据副作用 (P0 必测)

### Step 4: Generate Plan

生成 `api-test-plan.md`:
```yaml
feature_id: {feat_id}
plan_version: v1.0
source: ADR-047 pilot
anchor_type: feat
```

### Step 5: Generate Manifest

生成 `api-coverage-manifest.yaml`:
```yaml
api_coverage_manifest:
  feature_id: {feat_id}
  generated_at: {timestamp}
  source_plan_ref: {plan_path}
  items:
    - coverage_id: {coverage_id}
      capability: {capability_id}
      scenario_type: {type}
      dimension: {dimension}
      priority: {P0|P1|P2}
      source_feat_ref: {feat_ref}
      lifecycle_status: designed
      mapping_status: unmapped
      evidence_status: missing
      waiver_status: none
```

### Step 6: Apply Cut Rules

按优先级矩阵应用裁剪:
- P0: 仅裁剪 "幂等/并发" 和 "边界值 edge cases"
- P1: 裁剪 "边界值"、"状态约束"、"权限"、"幂等/并发"
- P2: 仅保留 "正常路径"

所有裁剪必须有 cut_record (含 approver + source_ref)。

## Output

- `api-test-plan.md`
- `api-coverage-manifest.yaml`

## Quality Checks

- [ ] coverage item count = capabilities × required dimensions
- [ ] 所有 P0 capabilities 有至少 5 个 coverage items
- [ ] 所有 cut 记录有 cut_record with approver + source_ref
- [ ] 所有 items lifecycle_status = designed
